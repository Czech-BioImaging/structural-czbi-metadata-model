#!/usr/bin/env python3
"""Rudimentary PySide6 GUI for editing a CZBIRD metadata record.

Design (matches the agreed spec)
--------------------------------
* One generic dialog class, :class:`CzbirdDialog`, edits ANY strict CZBIRD
  object. It introspects the object's pydantic fields and builds, top to bottom:
    - scalar fields (str/int/float/bool)  -> editable widgets;
    - a single nested CZBIRD field         -> an "Edit ..." button that opens
      that object's own CzbirdDialog (modal);
    - an array of CZBIRD objects           -> one "Edit" button per existing
      item plus a "+ Add" button that appends a fresh prefilled item;
    - an array of scalars                  -> an editable multi-line list + "+";
    - internal_id                          -> shown read-only (frozen/auto);
    - the profile discriminator (profile_type Literal) -> read-only label.

* Commit model = OPTION B (buffer-then-validate):
    - edits are held in the widgets, not written live to the model;
    - **Apply** validates + writes back into the model object, keeps dialog open;
    - **OK** does Apply, then closes;
    - **Cancel** discards changes to THIS object's scalar fields.
  (Nested objects opened from buttons commit through their own dialogs; because
  they are the same python objects held by the parent, their applied changes are
  already reflected in the parent's model.)

* The app boots from a prefilled, valid record (``prefill_Metadata``) so every
  dialog has data to show and every button can be clicked through immediately.

This is intentionally plain and sequential — no styling, no MVC. It is meant to
be readable and hackable rather than pretty.

Run:  python czbird_gui.py
Requires:  pip install PySide6
"""
from __future__ import annotations

import sys
from typing import Any, get_args, get_origin, Union
import types

from PySide6.QtWidgets import (
    QApplication, QDialog, QWidget, QLabel, QLineEdit, QSpinBox,
    QDoubleSpinBox, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout,
    QFormLayout, QGroupBox, QScrollArea, QPlainTextEdit, QMessageBox,
    QMainWindow, QRadioButton, QButtonGroup, QComboBox,
)
from PySide6.QtCore import Qt
from pydantic import BaseModel, ValidationError

from czbird import czbird_model as M
import czbird_prefill as P
import czbird_registry as R

# Session-wide resource registry, set once by MainWindow and read by dialogs.
REGISTRY: R.ResourceRegistry = R.ResourceRegistry()


# --------------------------------------------------------------------------- #
# Field classification (mirrors the model; drives which widget to build).
# --------------------------------------------------------------------------- #
def _is_czbird(t: Any) -> bool:
    return isinstance(t, type) and issubclass(t, BaseModel) and t is not M._Base


def classify(ann: Any):
    """Return a (kind, detail) tuple describing how to render a field.

    kind is one of:
      "scalar"       detail = python type (str/int/float/bool)
      "czbird"       detail = the CZBIRD class
      "list_scalar"  detail = python element type
      "list_czbird"  detail = the CZBIRD element class
      "union_czbird" detail = list of CZBIRD member classes (the profile union)
      "literal"      detail = tuple of allowed literal values
    """
    origin = get_origin(ann)

    if origin in (list, tuple):
        (inner,) = get_args(ann)
        ik, idetail = classify(inner)
        if ik == "czbird":
            return "list_czbird", idetail
        return "list_scalar", idetail

    if origin in (types.UnionType, Union):
        members = [a for a in get_args(ann) if _is_czbird(a)]
        if members:
            return "union_czbird", members
        non_none = [a for a in get_args(ann) if a is not type(None)]
        return classify(non_none[0]) if non_none else ("scalar", str)

    if _is_czbird(ann):
        return "czbird", ann

    if origin is not None and "Literal" in str(ann):
        return "literal", get_args(ann)

    if ann in (str, int, float, bool):
        return "scalar", ann

    return "scalar", str


def human(name: str) -> str:
    return name.replace("_", " ").capitalize()


def short(cls_name: str) -> str:
    return cls_name.replace("CZBIRD", "")


def _min_items(finfo) -> int:
    """Return the min_length constraint of a list field (0 if none)."""
    for meta in getattr(finfo, "metadata", ()):
        ml = getattr(meta, "min_length", None)
        if ml is not None:
            return ml
    return 0


def czbird_summary(obj: BaseModel) -> str:
    """Compact one-line summary of a nested object for row/field headers.

    OntologyTerm is abbreviated to ``OntoTerm: <term_label>`` so an array of
    ontology terms is scannable without opening each one. Other types fall back
    to their short class name plus an identifying label if present.
    """
    cls = type(obj).__name__
    if cls == "CZBIRDOntologyTerm":
        return f"OntoTerm: {getattr(obj, 'term_label', '') or '—'}"
    for key in ("title", "step_label", "data_label", "images_label",
                "record_title"):
        v = getattr(obj, key, None)
        if isinstance(v, str) and v:
            return f"{short(cls)}: {v}"
    return short(cls)


# --------------------------------------------------------------------------- #
# "Add resource" chooser: New vs. Copy-from an existing object.
# --------------------------------------------------------------------------- #
class AddResourceDialog(QDialog):
    """Choose the source for a resource object.

    Two regimes:

    * ``reset_mode=False`` (add a NEW item to a list): a radio pair — brand-new
      prefill, or a copy of an existing resource — plus a candidate dropdown.
      Returns an independent object (fresh id) via ``result_obj``.

    * ``reset_mode=True`` (fill the object currently being edited): there is no
      choice of "new object vs. copy" — the object already exists and is only
      being refilled. So the UI collapses to a single dropdown whose first entry
      is "Reset fields (empty placeholders)" and whose remaining entries are the
      other resources of this type (the currently-edited object is excluded —
      copying it into itself is pointless). ``result_obj`` is the raw source to
      copy fields FROM; the caller deep-copies the content.
    """

    RESET_LABEL = "Reset fields (empty placeholders)"

    def __init__(self, elem_cls: type, parent=None, reset_mode: bool = False,
                 exclude_obj: BaseModel | None = None):
        super().__init__(parent)
        self.elem_cls = elem_cls
        self.result_obj: BaseModel | None = None
        self._reset_mode = reset_mode
        self.setWindowTitle(f"Copy {short(elem_cls.__name__)} from…"
                            if reset_mode else f"Add {short(elem_cls.__name__)}")
        self.setMinimumWidth(460)

        current, deleted = REGISTRY.candidates(elem_cls)
        # Never offer the object being edited as a source for itself.
        if exclude_obj is not None:
            current = [o for o in current if o is not exclude_obj]
            deleted = [o for o in deleted if o is not exclude_obj]

        outer = QVBoxLayout(self)
        self._combo = QComboBox()

        if reset_mode:
            # ---- single-dropdown regime -------------------------------- #
            outer.addWidget(QLabel(
                f"Fill this {short(elem_cls.__name__)} from:"))
            self._combo_objs: list[BaseModel | None] = []
            # First entry = reset to placeholders (None => fresh prefill).
            self._combo.addItem(self.RESET_LABEL)
            self._combo_objs.append(None)
            for o in current:
                self._combo.addItem(czbird_summary(o))
                self._combo_objs.append(o)
            for o in deleted:
                self._combo.addItem(f"{czbird_summary(o)}   (removed)")
                self._combo_objs.append(o)
            outer.addWidget(self._combo)
            self._radio_new = None
            self._radio_copy = None
        else:
            # ---- add-new regime (radio pair + candidates) --------------- #
            outer.addWidget(QLabel(
                f"How should the new {short(elem_cls.__name__)} be created?"))
            self._radio_new = QRadioButton("Brand new (empty placeholders)")
            self._radio_copy = QRadioButton("Copy of an existing one:")
            self._radio_new.setChecked(True)
            grp = QButtonGroup(self)
            grp.addButton(self._radio_new)
            grp.addButton(self._radio_copy)
            outer.addWidget(self._radio_new)
            outer.addWidget(self._radio_copy)

            self._populate_combo(current, deleted)
            self._combo.setEnabled(False)
            outer.addWidget(self._combo)
            if not (current or deleted):
                self._radio_copy.setEnabled(False)
                self._combo.addItem("(no existing objects to copy)")
            self._radio_copy.toggled.connect(self._combo.setEnabled)

        row = QHBoxLayout()
        ok = QPushButton("Apply" if reset_mode else "Add")
        cancel = QPushButton("Cancel")
        ok.clicked.connect(self._on_ok)
        cancel.clicked.connect(self.reject)
        ok.setDefault(True)
        row.addStretch(1)
        row.addWidget(ok)
        row.addWidget(cancel)
        outer.addLayout(row)

    def _populate_combo(self, current, deleted) -> None:
        """Grouped candidate list, used only in add-new mode."""
        self._combo_objs: list[BaseModel | None] = []
        if current:
            self._combo.addItem("— current —")
            self._combo_objs.append(None)  # header, not selectable as a value
            for o in current:
                self._combo.addItem("  " + czbird_summary(o))
                self._combo_objs.append(o)
        if deleted:
            self._combo.addItem("— removed —")
            self._combo_objs.append(None)
            for o in deleted:
                self._combo.addItem("  " + czbird_summary(o))
                self._combo_objs.append(o)

    def _on_ok(self) -> None:
        if self._reset_mode:
            idx = self._combo.currentIndex()
            ref = self._combo_objs[idx] if 0 <= idx < len(self._combo_objs) else None
            # None at index 0 == "Reset fields" => a throwaway prefill source.
            # It is deliberately NOT registered: it is a scratch source, not an
            # object that lives in the record.
            self.result_obj = P.prefill(self.elem_cls) if ref is None else ref
            self.accept()
            return

        # add-new mode
        if self._radio_new.isChecked():
            self.result_obj = P.prefill(self.elem_cls)
        else:
            idx = self._combo.currentIndex()
            ref = self._combo_objs[idx] if 0 <= idx < len(self._combo_objs) else None
            if ref is None:  # header row or nothing chosen
                QMessageBox.information(
                    self, "Pick one", "Please select an object to copy.")
                return
            self.result_obj = R.copy_resource(ref)
        self.accept()


# --------------------------------------------------------------------------- #
# The generic editor dialog.
# --------------------------------------------------------------------------- #
class CzbirdDialog(QDialog):
    """Modal editor for a single strict CZBIRD object (option-B commit)."""

    def __init__(self, obj: BaseModel, parent: QWidget | None = None):
        super().__init__(parent)
        self.obj = obj
        self.setWindowTitle(f"Edit {short(type(obj).__name__)}")
        self.setMinimumWidth(520)

        # Widgets that hold scalar edits, keyed by field name. Each entry is a
        # callable returning the field's current value from its widget.
        self._scalar_getters: dict[str, callable] = {}
        # For scalar-list fields: field -> QPlainTextEdit (one value per line).
        self._list_scalar_widgets: dict[str, QPlainTextEdit] = {}
        # For an exclusive (radio) group: a single callable returning a dict of
        # {field: value_or_None} for all fields in the group.
        self._exclusive_getters: list[callable] = []

        outer = QVBoxLayout(self)

        # Scrollable body so deep objects with many fields stay usable.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        self.form = QFormLayout(body)
        self.form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        scroll.setWidget(body)
        outer.addWidget(scroll)

        self._build_fields()

        # Apply / OK / Cancel row (option B). For copy-enabled resource types a
        # "Fill from…" button sits at the bottom-left; it refills the current
        # object's fields from a chosen source (or resets to placeholders).
        btn_row = QHBoxLayout()
        if type(self.obj).__name__ in self._COPY_FROM_TYPES:
            copy_btn = QPushButton("Fill from…")
            copy_btn.clicked.connect(self._on_copy_from)
            btn_row.addWidget(copy_btn)
        btn_row.addStretch(1)
        apply_btn = QPushButton("Apply")
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        apply_btn.clicked.connect(self._on_apply)
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn.clicked.connect(self.reject)
        ok_btn.setDefault(True)
        for b in (apply_btn, ok_btn, cancel_btn):
            btn_row.addWidget(b)
        outer.addLayout(btn_row)

    # Resource types that offer an in-place "Fill from…" refill.
    _COPY_FROM_TYPES = {"CZBIRDMethod", "CZBIRDTool", "CZBIRDSpecimen"}

    # Classes whose (description, iri) pair is mutually exclusive: exactly one
    # is used at a time. Rendered as a radio group rather than two rows.
    _EXCLUSIVE_PAIR = {"CZBIRDMethod", "CZBIRDTool"}

    # ---------------------------------------------------------------- build --
    def _build_fields(self) -> None:
        cls_name = type(self.obj).__name__
        exclusive = cls_name in self._EXCLUSIVE_PAIR
        handled: set[str] = set()

        for name, finfo in type(self.obj).model_fields.items():
            if name in handled:
                continue
            kind, detail = classify(finfo.annotation)
            value = getattr(self.obj, name)

            # Exclusive description/iri pair -> one combined radio-group row.
            if exclusive and name in ("description", "iri"):
                self._add_exclusive_pair("description", "iri")
                handled.update({"description", "iri"})
                continue

            if name == "internal_id":
                self._add_readonly(name, value)
            elif kind == "literal":
                self._add_readonly(name, value)
            elif kind == "scalar":
                self._add_scalar(name, detail, value)
            elif kind == "list_scalar":
                self._add_list_scalar(name, value)
            elif kind == "czbird":
                self._add_single_czbird(name, value)
            elif kind == "list_czbird":
                min_required = _min_items(finfo)
                self._add_list_czbird(name, detail, value, min_required)
            elif kind == "union_czbird":
                # The root's was_generated_by: a single nested object whose
                # concrete class is whatever is currently set.
                self._add_single_czbird(name, value)

    def _add_readonly(self, name: str, value: Any) -> None:
        italic = name == "internal_id"
        style = "color: gray;" + (" font-style: italic;" if italic else "")

        value_lbl = QLabel(str(value))
        value_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        value_lbl.setStyleSheet(style)

        # Use an explicit styled label widget so the whole line (label + value)
        # is greyed/italicised, not just the value side.
        name_lbl = QLabel(f"{human(name)}:")
        name_lbl.setStyleSheet(style)
        self.form.addRow(name_lbl, value_lbl)

    def _add_scalar(self, name: str, pytype: type, value: Any) -> None:
        if pytype is bool:
            w = QCheckBox()
            w.setChecked(bool(value))
            self._scalar_getters[name] = w.isChecked
        elif pytype is int:
            w = QSpinBox()
            w.setRange(-10**9, 10**9)
            w.setValue(int(value) if value is not None else 0)
            self._scalar_getters[name] = w.value
        elif pytype is float:
            w = QDoubleSpinBox()
            w.setRange(-1e12, 1e12)
            w.setDecimals(3)
            w.setValue(float(value) if value is not None else 0.0)
            self._scalar_getters[name] = w.value
        else:  # str
            w = QLineEdit("" if value is None else str(value))
            self._scalar_getters[name] = w.text
        self.form.addRow(f"{human(name)}:", w)

    def _add_exclusive_pair(self, name_a: str, name_b: str) -> None:
        """Render two optional string fields as a mutually-exclusive choice.

        Exactly one of the two is active (radio-selected + editable); the other
        is disabled but still visible. The initially-selected radio is whichever
        field currently holds a non-empty value (falling back to the first).
        On collect, only the selected field is written; the other is set to
        ``None`` so the object never carries both at once.
        """
        val_a = getattr(self.obj, name_a) or ""
        val_b = getattr(self.obj, name_b) or ""

        box = QGroupBox(f"{human(name_a)} / {human(name_b)}  (choose one)")
        grid = QVBoxLayout(box)
        group = QButtonGroup(box)

        radio_a = QRadioButton(human(name_a))
        edit_a = QLineEdit(str(val_a))
        radio_b = QRadioButton(human(name_b))
        edit_b = QLineEdit(str(val_b))
        group.addButton(radio_a)
        group.addButton(radio_b)

        # Initial selection: prefer the one that already has content.
        select_b_first = bool(val_b) and not bool(val_a)
        radio_b.setChecked(select_b_first)
        radio_a.setChecked(not select_b_first)

        def _sync():
            edit_a.setEnabled(radio_a.isChecked())
            edit_b.setEnabled(radio_b.isChecked())

        radio_a.toggled.connect(_sync)
        radio_b.toggled.connect(_sync)
        _sync()

        for radio, edit in ((radio_a, edit_a), (radio_b, edit_b)):
            row = QWidget()
            rh = QHBoxLayout(row)
            rh.setContentsMargins(0, 0, 0, 0)
            rh.addWidget(radio)
            rh.addWidget(edit, 1)
            grid.addWidget(row)

        def getter() -> dict:
            if radio_a.isChecked():
                return {name_a: edit_a.text(), name_b: None}
            return {name_a: None, name_b: edit_b.text()}

        self._exclusive_getters.append(getter)
        self.form.addRow(box)

    def _add_list_scalar(self, name: str, value: list) -> None:
        box = QGroupBox(f"{human(name)} (one per line)")
        v = QVBoxLayout(box)
        editor = QPlainTextEdit("\n".join(str(x) for x in (value or [])))
        editor.setFixedHeight(70)
        v.addWidget(editor)
        self._list_scalar_widgets[name] = editor
        self.form.addRow(box)

    def _add_single_czbird(self, name: str, value: BaseModel) -> None:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        summary = QLabel(czbird_summary(value))
        summary.setStyleSheet("color: #555;")
        h.addWidget(summary)
        h.addStretch(1)
        btn = QPushButton(f"Edit {short(type(value).__name__)}…")

        def _open(_=False, o=value, lbl=summary):
            self._open_child(o)
            lbl.setText(czbird_summary(o))  # reflect edits made in the child

        btn.clicked.connect(_open)
        h.addWidget(btn)
        self.form.addRow(f"{human(name)}:", row)

    def _add_list_czbird(self, name: str, elem_cls: type, value: list,
                         min_required: int = 0) -> None:
        box = QGroupBox(f"{human(name)}  [{short(elem_cls.__name__)}]")
        v = QVBoxLayout(box)
        rows_holder = QWidget()
        rows_layout = QVBoxLayout(rows_holder)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        v.addWidget(rows_holder)

        def render_rows() -> None:
            # Clear and rebuild the item rows to reflect the live list.
            while rows_layout.count():
                item = rows_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            if not value:
                empty = QLabel("(none)")
                empty.setStyleSheet("color: #999; font-style: italic;")
                rows_layout.addWidget(empty)
            for idx, elem in enumerate(value):
                r = QWidget()
                rh = QHBoxLayout(r)
                rh.setContentsMargins(0, 0, 0, 0)
                row_lbl = QLabel(f"{idx + 1}. {czbird_summary(elem)}")
                rh.addWidget(row_lbl)
                rh.addStretch(1)
                edit_btn = QPushButton("Edit…")

                def _edit(_=False, o=elem):
                    self._open_child(o)
                    render_rows()  # labels may have changed

                edit_btn.clicked.connect(_edit)
                rh.addWidget(edit_btn)
                # Removal is blocked only when it would drop below the schema's
                # min_items for this field (0 for optional arrays -> can empty).
                del_btn = QPushButton("−")
                del_btn.setFixedWidth(28)
                def _remove(_=False, o=elem):
                    if len(value) > min_required:
                        value.remove(o)
                        # The removed object takes its whole subtree out of the
                        # record; move every resource in it to the deleted pool
                        # so they stop being "current" but remain copy sources.
                        REGISTRY.mark_deleted_tree(o)
                        render_rows()
                    else:
                        QMessageBox.information(
                            self, "Cannot remove",
                            f"At least {min_required} item(s) must remain.")
                del_btn.clicked.connect(_remove)
                rh.addWidget(del_btn)
                rows_layout.addWidget(r)

        def add_item(_=False) -> None:
            obj = P.prefill(elem_cls)
            # A prefilled object may contain a whole nested tree of resources
            # (a step creates a Method, a Tool, ...); register all of them so
            # they become available as "Fill from…" sources.
            REGISTRY.add_tree(obj)
            value.append(obj)
            render_rows()

        render_rows()
        add_btn = QPushButton(f"+ Add {short(elem_cls.__name__)}")
        add_btn.clicked.connect(add_item)
        v.addWidget(add_btn)
        self.form.addRow(box)

    # ------------------------------------------------------------- children --
    def _open_child(self, obj: BaseModel) -> None:
        dlg = CzbirdDialog(obj, self)
        dlg.exec()  # modal; child commits into the same object we hold

    # -------------------------------------------------------------- commit ---
    def _collect_scalars(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for name, getter in self._scalar_getters.items():
            data[name] = getter()
        for name, editor in self._list_scalar_widgets.items():
            lines = [ln for ln in editor.toPlainText().split("\n") if ln.strip() != ""]
            data[name] = lines
        for getter in self._exclusive_getters:
            data.update(getter())  # {selected: text, other: None}
        return data

    def _apply(self) -> bool:
        """Write scalar/list-scalar edits back into the model, validating.

        Returns True on success; shows a message box and returns False on a
        ValidationError. Nested CZBIRD objects are already live (edited via
        their own dialogs), so only this object's own scalar fields are written.
        """
        data = self._collect_scalars()
        try:
            for name, val in data.items():
                setattr(self.obj, name, val)  # validate_assignment fires here
            return True
        except ValidationError as e:
            # Roll back is unnecessary: assignment either succeeded or raised
            # per-field; report all messages.
            msgs = "\n".join(
                f"• {'.'.join(str(p) for p in err['loc'])}: {err['msg']}"
                for err in e.errors()
            )
            QMessageBox.critical(self, "Validation error", msgs)
            return False

    def _on_apply(self) -> None:
        self._apply()

    def _on_ok(self) -> None:
        if self._apply():
            self.accept()

    # ----------------------------------------------------------- copy-from --
    def _on_copy_from(self) -> None:
        """Refill this object's fields from a chosen source (or reset).

        Opens the chooser in reset mode. On accept, copies every non-id field
        from the source into the current object (keeping this object's own
        internal_id), then rebuilds the form so the new values are shown.
        """
        # Commit any in-progress scalar edits first so they are not lost, but
        # don't block on validation errors (the refill may fix them).
        try:
            for name, val in self._collect_scalars().items():
                setattr(self.obj, name, val)
        except ValidationError:
            pass

        dlg = AddResourceDialog(type(self.obj), self, reset_mode=True,
                                exclude_obj=self.obj)
        if dlg.exec() != QDialog.Accepted or dlg.result_obj is None:
            return
        R.copy_fields_into(self.obj, dlg.result_obj)
        self._rebuild_form()

    def _rebuild_form(self) -> None:
        """Clear and regenerate all field widgets from the current object."""
        self._scalar_getters.clear()
        self._list_scalar_widgets.clear()
        self._exclusive_getters.clear()
        while self.form.rowCount():
            self.form.removeRow(0)
        self._build_fields()


# --------------------------------------------------------------------------- #
# Main window: hosts the root record + a live JSON preview.
# --------------------------------------------------------------------------- #
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CZBIRD metadata editor (example)")
        self.record = P.prefill_Metadata()
        # Register every resource object already present in the starting record
        # so they are available as copy sources from the first click.
        REGISTRY.seed_from_record(self.record)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        layout.addWidget(QLabel(
            "<b>CZBIRD record editor</b> — starts from a prefilled valid record. "
            "Click <i>Edit record…</i> to drill in."))

        edit_btn = QPushButton("Edit record…")
        edit_btn.clicked.connect(self._edit_record)
        layout.addWidget(edit_btn)

        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview, 1)

        refresh_btn = QPushButton("Refresh JSON preview")
        refresh_btn.clicked.connect(self._refresh)
        layout.addWidget(refresh_btn)

        self._refresh()
        self.resize(640, 700)

    def _edit_record(self) -> None:
        CzbirdDialog(self.record, self).exec()
        self._refresh()

    def _refresh(self) -> None:
        self.preview.setPlainText(
            self.record.model_dump_json(indent=2, exclude_none=True))


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
