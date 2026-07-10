"""czbird_registry.py — a session-wide registry of "resource" objects.

Only strict classes that carry an ``internal_id`` are treated as reusable
resources. For each such type the registry keeps two live-reference lists:

  * ``current`` — objects presently attached somewhere in the record,
  * ``deleted`` — objects removed via the GUI's "−" button.

Both lists serve as copy sources in the "+ Add → Copy from…" dialog; deleted
objects stay available so a removed resource can be copied again later. Entries
are live references (not snapshots): a candidate reflects its latest edits, and
copying takes a deep, fresh-id snapshot at copy time.

The registry is intentionally tiny and framework-free so it can be unit-tested
without any GUI.
"""
from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel

from czbird import czbird_model as M


def _has_internal_id(cls: type) -> bool:
    return isinstance(cls, type) and issubclass(cls, BaseModel) \
        and "internal_id" in getattr(cls, "model_fields", {})


# The set of resource types (those with an internal_id).
RESOURCE_TYPES = {
    c for c in vars(M).values() if _has_internal_id(c) and c is not M._Base
}


class ResourceRegistry:
    """Per-type current/deleted lists of resource objects (by reference)."""

    def __init__(self) -> None:
        self._current: dict[type, list[BaseModel]] = {}
        self._deleted: dict[type, list[BaseModel]] = {}

    # -- population ------------------------------------------------------- #
    def seed_from_record(self, root: BaseModel) -> None:
        """Walk a record and register every resource object found in it."""
        self.add_tree(root)

    def add_tree(self, root: BaseModel) -> None:
        """Register every resource object in a (sub)tree as current.

        Prefill factories build whole nested trees (a new step silently creates
        a Method, a Tool, ontology terms, ...), so registering only the returned
        root object would leave everything beneath it invisible to the
        copy-from chooser. This registers the root and all its descendants.
        """
        for obj in _walk_models(root):
            if type(obj) in RESOURCE_TYPES:
                self.add_current(obj)

    def add_current(self, obj: BaseModel) -> None:
        """Register a live object as current (idempotent by identity)."""
        lst = self._current.setdefault(type(obj), [])
        if all(o is not obj for o in lst):
            lst.append(obj)
        # If it was previously deleted, bringing it back cancels that.
        dl = self._deleted.get(type(obj), [])
        self._deleted[type(obj)] = [o for o in dl if o is not obj]

    def mark_deleted(self, obj: BaseModel) -> None:
        """Move an object from current to deleted (kept as a copy source)."""
        cur = self._current.get(type(obj), [])
        self._current[type(obj)] = [o for o in cur if o is not obj]
        dl = self._deleted.setdefault(type(obj), [])
        if all(o is not obj for o in dl):
            dl.append(obj)

    def mark_deleted_tree(self, root: BaseModel) -> None:
        """Move every resource in a (sub)tree from current to deleted.

        Mirrors :meth:`add_tree`. Removing an object from the record orphans
        everything beneath it too (a removed step takes its Method, Tool and
        sinks with it), so those nested resources must stop being listed as
        "current" — while remaining available as copy sources.

        Note this whole-subtree sweep is only correct because objects in this
        design are never shared between two parents: "Copy from…" produces
        independent objects (fresh internal_ids) and reference-reuse was
        deliberately not implemented. If shared references were ever
        introduced, a nested object would have to stay `current` while it is
        still reachable from somewhere else in the record, and this would need
        a reachability check against the live record instead.
        """
        for obj in _walk_models(root):
            if type(obj) in RESOURCE_TYPES:
                self.mark_deleted(obj)

    # -- queries ---------------------------------------------------------- #
    def current(self, cls: type) -> list[BaseModel]:
        return list(self._current.get(cls, []))

    def deleted(self, cls: type) -> list[BaseModel]:
        return list(self._deleted.get(cls, []))

    def candidates(self, cls: type) -> tuple[list[BaseModel], list[BaseModel]]:
        """Return (current, deleted) copy-source lists for a type."""
        return self.current(cls), self.deleted(cls)


def copy_resource(ref: BaseModel) -> BaseModel:
    """Deep-copy a resource and give the copy (and every nested resource in it)
    a fresh internal_id, so the copy is independent and the record-level
    uniqueness guard is satisfied.
    """
    clone = ref.model_copy(deep=True)
    _refresh_ids(clone)
    return clone


def copy_fields_into(target: BaseModel, source: BaseModel) -> None:
    """Overwrite ``target``'s fields in place from ``source``, keeping target's
    own ``internal_id``.

    Every non-id field is deep-copied from the source so the two objects share
    no nested references; nested resource objects in the copied content get
    fresh internal_ids. Frozen fields (internal_id) are left untouched.
    Assignment uses object.__setattr__ to bypass per-field validation during the
    bulk fill; the caller is expected to validate afterwards (the GUI does, on
    Apply/OK).
    """
    for name, finfo in type(target).model_fields.items():
        if name == "internal_id" or bool(getattr(finfo, "frozen", False)):
            continue
        src_val = getattr(source, name)
        new_val = _deep_copy_value(src_val)
        _refresh_ids(new_val)
        object.__setattr__(target, name, new_val)


def _deep_copy_value(val):
    if isinstance(val, BaseModel):
        return val.model_copy(deep=True)
    if isinstance(val, list):
        return [_deep_copy_value(v) for v in val]
    if isinstance(val, tuple):
        return tuple(_deep_copy_value(v) for v in val)
    return val


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _walk_models(obj: object) -> Iterable[BaseModel]:
    if isinstance(obj, BaseModel):
        yield obj
        for name in type(obj).model_fields:
            yield from _walk_models(getattr(obj, name))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from _walk_models(item)


def _refresh_ids(obj: object) -> None:
    """Assign a brand-new internal_id to every resource object in a tree.

    internal_id is frozen, so we bypass assignment validation with
    object.__setattr__ — this is safe because the value we set is freshly
    generated to satisfy the field's pattern.
    """
    if isinstance(obj, BaseModel):
        if "internal_id" in type(obj).model_fields:
            object.__setattr__(obj, "internal_id", M.make_internal_id())
        for name in type(obj).model_fields:
            _refresh_ids(getattr(obj, name))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _refresh_ids(item)
