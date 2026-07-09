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
    QMainWindow,
)
from PySide6.QtCore import Qt
from pydantic import BaseModel, ValidationError

from czbird import czbird_model as M
import czbird_prefill as P


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

        # Apply / OK / Cancel row (option B).
        btn_row = QHBoxLayout()
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

    # ---------------------------------------------------------------- build --
    def _build_fields(self) -> None:
        for name, finfo in type(self.obj).model_fields.items():
            kind, detail = classify(finfo.annotation)
            value = getattr(self.obj, name)

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
                self._add_list_czbird(name, detail, value)
            elif kind == "union_czbird":
                # The root's was_generated_by: a single nested object whose
                # concrete class is whatever is currently set.
                self._add_single_czbird(name, value)

    def _add_readonly(self, name: str, value: Any) -> None:
        lbl = QLabel(str(value))
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setStyleSheet("color: gray;")
        self.form.addRow(f"{human(name)}:", lbl)

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
        h.addWidget(QLabel(f"<i>{short(type(value).__name__)}</i>"))
        h.addStretch(1)
        btn = QPushButton(f"Edit {short(type(value).__name__)}…")
        btn.clicked.connect(lambda _=False, o=value: self._open_child(o))
        h.addWidget(btn)
        self.form.addRow(f"{human(name)}:", row)

    def _add_list_czbird(self, name: str, elem_cls: type, value: list) -> None:
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
            for idx, elem in enumerate(value):
                r = QWidget()
                rh = QHBoxLayout(r)
                rh.setContentsMargins(0, 0, 0, 0)
                rh.addWidget(QLabel(f"{idx + 1}. {short(type(elem).__name__)}"))
                rh.addStretch(1)
                edit_btn = QPushButton("Edit…")
                edit_btn.clicked.connect(lambda _=False, o=elem: self._open_child(o))
                rh.addWidget(edit_btn)
                # Allow removing extra items, but never below one (min_items
                # safety for required arrays; harmless for optional ones).
                del_btn = QPushButton("−")
                del_btn.setFixedWidth(28)
                def _remove(_=False, o=elem):
                    if len(value) > 1:
                        value.remove(o)
                        render_rows()
                    else:
                        QMessageBox.information(
                            self, "Cannot remove",
                            "At least one item must remain.")
                del_btn.clicked.connect(_remove)
                rh.addWidget(del_btn)
                rows_layout.addWidget(r)

        def add_item(_=False) -> None:
            value.append(P.prefill(elem_cls))
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


# --------------------------------------------------------------------------- #
# Main window: hosts the root record + a live JSON preview.
# --------------------------------------------------------------------------- #
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CZBIRD metadata editor (example)")
        self.record = P.prefill_Metadata()

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
