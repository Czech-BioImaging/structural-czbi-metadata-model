#!/usr/bin/env python3
"""Generate Pydantic v2 models (one class per CZBIRD object) from the NRP YAML schema.

Design decisions:
  * Every model sets ``validate_assignment=True`` so attribute assignment is
    re-validated (the "setters with type checking" requirement).
  * ``extra="forbid"`` mirrors NRP's ``dynamic: strict`` object mapping.
  * NRP scalar types collapse to Python scalars:
        keyword / fulltext / fulltext+keyword -> str
        boolean -> bool, int/long -> int, float/double -> float
  * ``array`` -> ``list[item]``; ``min_items`` -> ``Field(min_length=...)``.
  * References to other CZBIRD types become the corresponding class.
  * The ``polymorphic`` root field becomes a discriminated union keyed on the
    profile_type Literal carried by each profile class.
"""
from __future__ import annotations

import sys
import yaml

SCALAR = {
    "keyword": "str",
    "fulltext": "str",
    "fulltext+keyword": "str",
    "boolean": "bool",
    "int": "int",
    "long": "int",
    "float": "float",
    "double": "float",
    "date": "str",
    "datetime": "str",
    "time": "str",
}

# Maps a polymorphic member class name -> (discriminator_field, literal_value),
# filled while parsing every polymorphic field (on any class, not just
# Metadata). Each member class gets a Literal[...] on its discriminator field.
POLY_MEMBER_DISCRIMINATOR: dict[str, tuple[str, str]] = {}


def is_czbird(t: str) -> bool:
    return t.startswith("CZBIRD")


def py_item_type(item: dict) -> str:
    """Python type for an array item."""
    t = item["type"]
    if t in SCALAR:
        return SCALAR[t]
    if is_czbird(t):
        return t
    raise ValueError(f"Unsupported array item type: {t}")


def render_field(name: str, spec: dict) -> tuple[str, str]:
    """Return (annotation, field_default_expr) for one property."""
    t = spec["type"]
    required = spec.get("required", False)

    if t == "array":
        inner = py_item_type(spec["items"])
        ann = f"list[{inner}]"
        constraints = []
        if "min_items" in spec:
            constraints.append(f"min_length={spec['min_items']}")
        if "max_items" in spec:
            constraints.append(f"max_length={spec['max_items']}")
        if spec.get("unique_items"):
            # enforced via validator note; pydantic has no builtin unique
            pass
        if required:
            field = f"Field({', '.join(constraints)})" if constraints else "Field(...)"
            return ann, field
        else:
            # Optional array: the field may be absent (None), but if present it
            # must satisfy min_items — an empty list is NOT allowed. So default
            # to None (not []), and keep the min_length/max_length constraints,
            # which apply only when a list is actually provided.
            joined = ", ".join(["default=None", *constraints])
            return f"Optional[{ann}]", f"Field({joined})"

    if t in SCALAR:
        ann = SCALAR[t]
    elif is_czbird(t):
        ann = t
    else:
        raise ValueError(f"Unsupported field type: {t} on {name}")

    if required:
        return ann, "Field(...)"
    return f"Optional[{ann}]", "Field(default=None)"


def render_object(name: str, body: dict) -> str:
    props = body.get("properties", {})
    lines = [f"class {name}(_Base):"]

    # If this class is a member of some polymorphic union, it carries a fixed
    # Literal on its discriminator field (e.g. profile_type / description_type).
    disc_field, disc_value = POLY_MEMBER_DISCRIMINATOR.get(name, (None, None))

    if not props:
        lines.append("    pass")
        return "\n".join(lines) + "\n"

    body_lines: list[str] = []
    for pname, spec in props.items():
        if pname == disc_field and disc_value is not None:
            body_lines.append(
                f'    {pname}: Literal["{disc_value}"] = Field(...)'
            )
            continue
        if spec.get("type") == "polymorphic":
            # Inline polymorphic field on a regular class: emit its union alias.
            alias, _ = render_polymorphic_alias(spec)
            if spec.get("required", False):
                body_lines.append(f"    {pname}: {alias} = Field(...)")
            else:
                body_lines.append(
                    f"    {pname}: Optional[{alias}] = Field(default=None)")
            continue
        ann, field = render_field(pname, spec)
        body_lines.append(f"    {pname}: {ann} = {field}")

    lines.extend(body_lines)
    return "\n".join(lines) + "\n"


def render_polymorphic_alias(field_spec: dict) -> tuple[str, list[str]]:
    """Return (union_type_expr, member_class_names) for a polymorphic field.

    Records, for each member class, which discriminator field it must carry and
    the literal value it takes there — so member classes on any polymorphic
    union (not only Metadata's profiles) get the right Literal[...] injected.
    """
    disc = field_spec.get("discriminator", "type")
    members = []
    for branch in field_spec["oneof"]:
        cls = branch["type"]
        POLY_MEMBER_DISCRIMINATOR[cls] = (disc, branch["discriminator"])
        members.append(cls)
    union = " | ".join(members)
    alias = f'Annotated[{union}, Field(discriminator="{disc}")]'
    return alias, members


def main(path: str, out_path: str = "czbird_model.py") -> None:
    with open(path) as f:
        schema = yaml.safe_load(f)

    # Discovery pass: scan EVERY class (not just Metadata) for polymorphic
    # fields, so each union member's discriminator field+literal is registered
    # before any class is rendered — regardless of definition order. This makes
    # polymorphic fields work on regular classes (e.g. CZBIRDTool.tool_description),
    # not only on the Metadata root.
    for cname, cbody in schema.items():
        for pname, spec in (cbody.get("properties", {}) or {}).items():
            if isinstance(spec, dict) and spec.get("type") == "polymorphic":
                render_polymorphic_alias(spec)

    # The root's polymorphic field alias (was_generated_by) for the Metadata body.
    root = schema["Metadata"]
    poly_alias = None
    for pname, spec in root["properties"].items():
        if spec.get("type") == "polymorphic":
            poly_alias, _ = render_polymorphic_alias(spec)
            root_poly_field = pname
            root_poly_required = spec.get("required", False)

    header = '''"""CZBIRD metadata model — Pydantic v2 models generated from metadata.yaml.

AUTO-GENERATED — do not edit by hand. Regenerate with:

    python generate.py metadata.yaml -o czbird/czbird_model.py

Each class validates on construction AND on attribute assignment
(validate_assignment=True), giving type-checked setters without hand-written
@property code.
"""
from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,   # re-validate on every attribute set
        extra="forbid",             # mirrors NRP dynamic: strict
        validate_default=True,
    )
'''

    out = [header]

    # Render every object type in definition order (leaves first, as in the
    # YAML, so forward references stay minimal — but from __future__ import
    # annotations makes ordering irrelevant anyway).
    for name, body in schema.items():
        if name == "Metadata":
            continue
        out.append(render_object(name, body))

    # Root Metadata class, with the polymorphic union field.
    meta_lines = ["class Metadata(_Base):"]
    for pname, spec in root["properties"].items():
        if spec.get("type") == "polymorphic":
            req = spec.get("required", False)
            if req:
                meta_lines.append(f"    {pname}: {poly_alias} = Field(...)")
            else:
                meta_lines.append(
                    f"    {pname}: Optional[{poly_alias}] = Field(default=None)"
                )
            continue
        ann, field = render_field(pname, spec)
        meta_lines.append(f"    {pname}: {ann} = {field}")
    out.append("\n".join(meta_lines) + "\n")

    # Rebuild for forward refs.
    out.append("\nMetadata.model_rebuild()\n")

    code = "\n\n".join(out)
    with open(out_path, "w") as f:
        f.write(code)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Generate czbird_model.py (Pydantic v2) from the NRP YAML schema.")
    ap.add_argument("yaml", nargs="?", default="metadata.yaml",
                    help="path to metadata.yaml (default: ./metadata.yaml)")
    ap.add_argument("-o", "--out", default="czbird_model.py",
                    help="output .py path (default: ./czbird_model.py)")
    args = ap.parse_args()
    main(args.yaml, args.out)
