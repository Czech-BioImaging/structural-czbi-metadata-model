"""Draft (partial-fill) twins of the strict CZBIRD metadata models.

Purpose
-------
The strict models in ``czbird_model`` validate required fields at construction,
so a genuinely empty instance with missing required fields cannot exist. This
module provides an *editing buffer*: for every strict model ``CZBIRDFoo`` there
is a ``CZBIRDFooDraft`` where

  * every field is optional and defaults to unset (``None``),
  * nested CZBIRD references point at the corresponding *draft* twin (so you can
    partially fill sub-objects too, to any depth),
  * ``validate_assignment=True`` is kept, so each attribute assignment is still
    type-checked at assignment time,
  * the polymorphic ``was_generated_by`` union loses its discriminator
    requirement (you may fill a profile before its ``profile_type`` is set).

Typical workflow
----------------
    d = MetadataDraft()                       # empty, no error
    d.record_title = "My record"              # type-checked on assign
    d.publication_year = "2025"               # ValidationError: not an int
    d.publication_year = 2025                 # ok
    json_str = d.model_dump_json(exclude_none=True)   # export partial data

    # When the record is believed complete, promote to the strict model. This
    # is where "you forgot a required field" finally surfaces:
    strict = to_strict(d, czbird_model.Metadata)      # -> validated Metadata

Notes
-----
* ``None`` here means "unset". This module does not distinguish "never touched"
  from "deliberately null"; if you need that, track filled keys separately.
* ``extra="forbid"`` is preserved, so a stray attribute is still rejected.
* The profile union is *undiscriminated* in draft form. When you reload a bare
  nested dict like ``{"was_generated_by": {"profile_type": "rawData"}}`` the
  first structurally-compatible profile draft is chosen, which may not be the
  one named by ``profile_type`` (all four drafts are all-optional and thus
  similar in shape). This does not affect correctness on promotion: ``to_strict``
  re-applies the real discriminator and routes to the right strict profile. If
  you build the profile draft explicitly (``full.was_generated_by =
  CZBIRDRawDataProfileDraft(...)``) there is no ambiguity.
"""
from __future__ import annotations

import types
import typing
from typing import Optional, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, create_model

import czbird.czbird_model as _strict


# --------------------------------------------------------------------------- #
# Build one draft twin per strict model, in dependency-safe order.
# --------------------------------------------------------------------------- #

# All strict model classes defined in czbird_model, in their definition order.
_STRICT_CLASSES: list[type[BaseModel]] = [
    obj
    for obj in vars(_strict).values()
    if isinstance(obj, type)
    and issubclass(obj, BaseModel)
    and obj.__module__ == _strict.__name__
    and obj is not _strict._Base
]

# strict class  ->  draft class (filled in progressively below)
_STRICT_TO_DRAFT: dict[type[BaseModel], type[BaseModel]] = {}

_DRAFT_CONFIG = ConfigDict(validate_assignment=True, extra="forbid")


def _draftify_annotation(ann: typing.Any) -> typing.Any:
    """Rewrite a strict field annotation into its draft-relaxed equivalent.

    * A strict CZBIRD model reference -> its draft twin.
    * list[X] / tuple[X] etc. -> same container over draftified args.
    * Union[...] (incl. the discriminated profile union) -> Union of
      draftified members; the pydantic discriminator (applied via Annotated in
      the strict model) is intentionally not reproduced here.
    * Anything else (str, int, float, bool, Optional[...], etc.) -> unchanged.
    """
    # Direct reference to a strict model -> its draft.
    if isinstance(ann, type) and ann in _STRICT_TO_DRAFT:
        return _STRICT_TO_DRAFT[ann]

    origin = get_origin(ann)
    if origin is None:
        return ann  # plain scalar / already-fine type

    args = get_args(ann)
    new_args = tuple(_draftify_annotation(a) for a in args)

    # Union (both typing.Union and the X | Y form).
    if origin is Union or origin is types.UnionType:
        return Union[new_args]  # type: ignore[valid-type]

    # Generic container such as list[...] / tuple[...] / dict[...].
    try:
        return origin[new_args] if len(new_args) != 1 else origin[new_args[0]]
    except TypeError:
        # Fallback for builtins that need subscripting via typing form.
        return ann


# Fields the draft layer never exposes. ``internal_id`` is auto-generated and
# frozen on the strict model; per the builder-pattern design it is minted only
# when ``to_strict`` constructs the real object, never during draft editing.
_DRAFT_EXCLUDED_FIELDS = {"internal_id"}


def _build_draft(strict_cls: type[BaseModel]) -> type[BaseModel]:
    fields: dict[str, tuple] = {}
    for name, finfo in strict_cls.model_fields.items():
        if name in _DRAFT_EXCLUDED_FIELDS:
            continue
        relaxed = _draftify_annotation(finfo.annotation)
        # Every field becomes optional & unset by default.
        fields[name] = (Optional[relaxed], None)
    return create_model(
        f"{strict_cls.__name__}Draft",
        __config__=_DRAFT_CONFIG,
        **fields,
    )


# Two-pass build so nested references resolve to draft twins:
#   pass 1: register placeholder draft classes for every strict class,
#   pass 2: (re)build with fields, now that _STRICT_TO_DRAFT is populated.
for _cls in _STRICT_CLASSES:
    _STRICT_TO_DRAFT[_cls] = None  # type: ignore[assignment]  # reserve slot

# Because create_model needs the map populated to rewrite nested refs, build in
# an order where each class's dependencies already have a draft. czbird_model is
# authored leaf-first, so a single forward pass with model_rebuild at the end
# works. We build, then rebuild to resolve any forward references.
for _cls in _STRICT_CLASSES:
    _STRICT_TO_DRAFT[_cls] = _build_draft(_cls)

for _draft in _STRICT_TO_DRAFT.values():
    _draft.model_rebuild()


# --------------------------------------------------------------------------- #
# Public names: expose each draft as CZBIRD...Draft / MetadataDraft.
# --------------------------------------------------------------------------- #
_g = globals()
for _cls, _draft in _STRICT_TO_DRAFT.items():
    _g[_draft.__name__] = _draft

__all__ = [d.__name__ for d in _STRICT_TO_DRAFT.values()] + [
    "to_strict",
    "draft_for",
    "missing_required",
]


def draft_for(strict_cls: type[BaseModel]) -> type[BaseModel]:
    """Return the draft twin class for a given strict CZBIRD model class."""
    return _STRICT_TO_DRAFT[strict_cls]


def to_strict(draft: BaseModel, strict_cls: type[BaseModel]) -> BaseModel:
    """Promote a (believed-complete) draft into a fully-validated strict model.

    Raises ``pydantic.ValidationError`` reporting *all* problems at once
    (missing required fields, type errors deep in the tree, discriminator
    resolution, min_items, extra fields) with dotted paths.
    """
    return strict_cls.model_validate(draft.model_dump(exclude_none=True))


def missing_required(draft: BaseModel, strict_cls: type[BaseModel]) -> list[str]:
    """Best-effort list of dotted paths to required fields not yet filled.

    Convenience for a UI ("what's left before this can be submitted?"). It walks
    the strict schema against the draft's currently-set values. This is a
    shallow-to-deep check; the authoritative gate remains ``to_strict``.
    """
    missing: list[str] = []

    def walk(d: BaseModel, s_cls: type[BaseModel], prefix: str) -> None:
        for name, finfo in s_cls.model_fields.items():
            if name in _DRAFT_EXCLUDED_FIELDS:
                continue  # auto-filled at strict construction, never user-supplied
            value = getattr(d, name, None)
            path = f"{prefix}{name}"
            if finfo.is_required() and value is None:
                missing.append(path)
            # Recurse into nested drafts / lists of drafts when present.
            if value is None:
                continue
            ann = finfo.annotation
            sub = _strict_member(ann)
            if sub is not None and isinstance(value, BaseModel):
                walk(value, sub, path + ".")
            elif isinstance(value, list):
                elem = _strict_member(get_args(ann)[0]) if get_args(ann) else None
                if elem is not None:
                    for i, item in enumerate(value):
                        if isinstance(item, BaseModel):
                            walk(item, elem, f"{path}.{i}.")

    walk(draft, strict_cls, "")
    return missing


def _strict_member(ann: typing.Any) -> Optional[type[BaseModel]]:
    """If ``ann`` refers (directly) to a strict CZBIRD model, return it."""
    if isinstance(ann, type) and issubclass(ann, BaseModel) and ann in _STRICT_TO_DRAFT:
        return ann
    for a in get_args(ann):
        if isinstance(a, type) and a in _STRICT_TO_DRAFT:
            return a
    return None
