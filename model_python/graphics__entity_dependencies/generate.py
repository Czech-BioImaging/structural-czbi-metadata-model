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

# Maps a profile class name -> its discriminator literal value, filled while
# parsing the polymorphic root field.
PROFILE_DISCRIMINATOR: dict[str, str] = {}


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
            # optional array -> default empty list
            joined = ", ".join(["default_factory=list", *constraints])
            return f"{ann}", f"Field({joined})"

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

    # Special-case: profile classes carry a fixed profile_type literal.
    disc_value = PROFILE_DISCRIMINATOR.get(name)

    if not props:
        lines.append("    pass")
        return "\n".join(lines) + "\n"

    body_lines: list[str] = []
    for pname, spec in props.items():
        if pname == "profile_type" and disc_value is not None:
            body_lines.append(
                f'    profile_type: Literal["{disc_value}"] = Field(...)'
            )
            continue
        ann, field = render_field(pname, spec)
        body_lines.append(f"    {pname}: {ann} = {field}")

    lines.extend(body_lines)
    return "\n".join(lines) + "\n"


def render_polymorphic_alias(field_spec: dict) -> tuple[str, list[str]]:
    """Return (union_type_expr, member_class_names) for a polymorphic field."""
    disc = field_spec.get("discriminator", "type")
    members = []
    for branch in field_spec["oneof"]:
        cls = branch["type"]
        PROFILE_DISCRIMINATOR[cls] = branch["discriminator"]
        members.append(cls)
    union = " | ".join(members)
    alias = f'Annotated[{union}, Field(discriminator="{disc}")]'
    return alias, members


def main(path: str) -> None:
    with open(path) as f:
        schema = yaml.safe_load(f)

    # First pass: discover the polymorphic root field so profile classes know
    # their discriminator literals before we render them.
    root = schema["Metadata"]
    poly_alias = None
    for pname, spec in root["properties"].items():
        if spec.get("type") == "polymorphic":
            poly_alias, _ = render_polymorphic_alias(spec)
            root_poly_field = pname
            root_poly_required = spec.get("required", False)

    header = '''"""CZBIRD metadata model — Pydantic v2 models generated from metadata.yaml.

Auto-generated. Each class validates on construction AND on attribute
assignment (model_config validate_assignment=True), giving you type-checked
setters without hand-written @property code.
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
    with open("/home/claude/gen/czbird_model.py", "w") as f:
        f.write(code)
    print("wrote czbird_model.py")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "metadata.yaml")
