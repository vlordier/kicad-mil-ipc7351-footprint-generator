# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application window — PySide6-based desktop UI.

Fully wired: wizard -> calculator -> preview -> export.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStatusBar,
    QToolBar,
    QTabWidget,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QIcon

from ..core.calculator import FootprintCalculator
from ..core.ipc7351 import PackageDefinition, BodyDimensions, LeadDimensions, Tolerance
from ..core.validation import IPCValidator, Severity
from ..export.kicad_mod import KiCadModExporter
from ..export.report import PDFReportGenerator
from .preview import FootprintPreview


class MainWindow(QMainWindow):
    """Top-level window for the footprint generator application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KiCad MIL IPC-7351 Footprint Generator v0.1.0")
        self.setMinimumSize(1400, 900)

        self._calculator = FootprintCalculator()
        self._last_result = None

        self._setup_actions()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_statusbar()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _setup_actions(self):
        self.act_quit = QAction("&Quit", self)
        self.act_quit.setShortcut("Ctrl+Q")
        self.act_quit.triggered.connect(self.close)

        self.act_open = QAction("&Open Library...", self)
        self.act_open.setShortcut("Ctrl+O")
        self.act_open.triggered.connect(self._open_library)

        self.act_export = QAction("&Export Footprint...", self)
        self.act_export.setShortcut("Ctrl+E")
        self.act_export.triggered.connect(self._export_footprint)

        self.act_batch = QAction("&Batch Import (CSV)...", self)
        self.act_batch.setShortcut("Ctrl+B")
        self.act_batch.triggered.connect(self._batch_import)

        self.act_report = QAction("Generate &Report...", self)
        self.act_report.setShortcut("Ctrl+R")
        self.act_report.triggered.connect(self._generate_report)

        self.act_generate = QAction("&Generate", self)
        self.act_generate.setShortcut("Ctrl+G")
        self.act_generate.triggered.connect(self._generate)

        self.act_about = QAction("&About", self)
        self.act_about.triggered.connect(self._show_about)

    # ------------------------------------------------------------------
    # Menu & Toolbar
    # ------------------------------------------------------------------

    def _setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.act_open)
        file_menu.addAction(self.act_batch)
        file_menu.addAction(self.act_export)
        file_menu.addSeparator()
        file_menu.addAction(self.act_quit)

        gen_menu = menubar.addMenu("&Generate")
        gen_menu.addAction(self.act_generate)
        gen_menu.addAction(self.act_report)

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.act_about)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main")
        toolbar.addAction(self.act_generate)
        toolbar.addAction(self.act_export)
        toolbar.addAction(self.act_batch)
        toolbar.addAction(self.act_report)
        self.addToolBar(toolbar)

    # ------------------------------------------------------------------
    # Central Widget — split pane: input | preview | validation
    # ------------------------------------------------------------------

    def _setup_central_widget(self):
        splitter = QSplitter(Qt.Horizontal)

        # Left: input form
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(self._build_input_panel())

        # Middle: preview + output
        middle = QWidget()
        middle_layout = QVBoxLayout(middle)
        self.preview = FootprintPreview()
        middle_layout.addWidget(self.preview)
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setMaximumHeight(150)
        middle_layout.addWidget(self.output_log)

        # Right: validation results
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("Validation Results"))
        self.validation_table = QTableWidget(0, 4)
        self.validation_table.setHorizontalHeaderLabels(["Severity", "Rule", "Message", "Value"])
        self.validation_table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self.validation_table)

        splitter.addWidget(left)
        splitter.addWidget(middle)
        splitter.addWidget(right)
        splitter.setSizes([400, 600, 400])

        self.setCentralWidget(splitter)

    def _build_input_panel(self) -> QWidget:
        panel = QGroupBox("Package Parameters")
        form = QFormLayout()

        self.family_combo = QComboBox()
        self.family_combo.addItems([
            "chip", "sod", "sot", "soic", "tssop",
            "qfp", "qfn", "dfn", "bga", "lga", "csp",
            "dip", "sip", "axial", "radial",
        ])
        form.addRow("Family:", self.family_combo)

        self.density_combo = QComboBox()
        self.density_combo.addItems(["A (Most — MIL)", "B (Nominal)", "C (Least)"])
        form.addRow("Density:", self.density_combo)

        self.mil_check = QCheckBox("Apply MIL Derating")
        self.mil_check.setChecked(True)
        form.addRow(self.mil_check)

        form.addRow(QLabel("Body Dimensions (mm)"))
        self.body_length = self._spin(0.1, 200.0, 3.2)
        self.body_length_tol = self._spin(0.0, 10.0, 0.1)
        self.body_width = self._spin(0.1, 200.0, 1.6)
        self.body_width_tol = self._spin(0.0, 10.0, 0.1)
        self.body_height = self._spin(0.01, 50.0, 0.55)
        form.addRow("Length:", self.body_length)
        form.addRow("Length Tol ±:", self.body_length_tol)
        form.addRow("Width:", self.body_width)
        form.addRow("Width Tol ±:", self.body_width_tol)
        form.addRow("Height:", self.body_height)

        form.addRow(QLabel("Lead Dimensions (mm)"))
        self.lead_count = QSpinBox()
        self.lead_count.setRange(0, 1000)
        self.lead_pitch = self._spin(0.1, 50.0, 1.27)
        self.lead_width = self._spin(0.01, 10.0, 0.4)
        self.lead_length = self._spin(0.01, 10.0, 1.0)
        form.addRow("Count:", self.lead_count)
        form.addRow("Pitch:", self.lead_pitch)
        form.addRow("Width:", self.lead_width)
        form.addRow("Length:", self.lead_length)

        form.addRow(QLabel("BGA (mm)"))
        self.ball_diameter = self._spin(0.1, 5.0, 0.5)
        self.ball_count = QSpinBox()
        self.ball_count.setRange(0, 10000)
        self.ball_count.setValue(256)
        form.addRow("Ball Dia:", self.ball_diameter)
        form.addRow("Ball Count:", self.ball_count)

        gen_btn = QPushButton("Generate Footprint (Ctrl+G)")
        gen_btn.clicked.connect(self._generate)
        form.addRow(gen_btn)

        panel.setLayout(form)
        return panel

    @staticmethod
    def _spin(min_v: float, max_v: float, default: float) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(min_v, max_v)
        s.setDecimals(3)
        s.setValue(default)
        return s

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    def _setup_statusbar(self):
        self.status = QStatusBar()
        self.status.showMessage("Ready — configure parameters and press Generate")
        self.setStatusBar(self.status)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot()
    def _generate(self) -> None:
        try:
            density = self.density_combo.currentText()[0]
            pkg = PackageDefinition(
                family=self.family_combo.currentText(),
                body=BodyDimensions(
                    length=Tolerance(self.body_length.value(), self.body_length_tol.value(), self.body_length_tol.value()),
                    width=Tolerance(self.body_width.value(), self.body_width_tol.value(), self.body_width_tol.value()),
                    height=Tolerance(self.body_height.value(), self.body_height.value() * 0.1, self.body_height.value() * 0.1),
                ),
            )
            if self.lead_count.value() > 0:
                pkg.leads = LeadDimensions(
                    width=Tolerance(self.lead_width.value(), self.lead_width.value() * 0.1, self.lead_width.value() * 0.1),
                    length=Tolerance(self.lead_length.value(), self.lead_length.value() * 0.1, self.lead_length.value() * 0.1),
                    pitch=Tolerance(self.lead_pitch.value(), 0.0, 0.0),
                    count=self.lead_count.value(),
                )
            if self.ball_diameter.value() > 0 and self.ball_count.value() > 0:
                pkg.ball_diameter = Tolerance(self.ball_diameter.value(), 0.0, 0.0)
                pkg.ball_count = self.ball_count.value()

            self._calculator = FootprintCalculator()
            self._last_result = self._calculator.calculate(pkg, density=density)

            if self.mil_check.isChecked():
                self._last_result = self._calculator.apply_mil_derating(self._last_result)

            self.preview.render(self._last_result)
            self._update_validation()
            self._log_result()
            self.status.showMessage(f"Generated: {self._last_result.pads[0].width:.3f} x {self._last_result.pads[0].height:.3f} mm")
        except Exception as e:
            self.status.showMessage(f"Error: {e}")
            QMessageBox.critical(self, "Generation Error", str(e))

    def _update_validation(self) -> None:
        if self._last_result is None:
            return
        validator = IPCValidator(self._last_result)
        issues = validator.validate()
        self.validation_table.setRowCount(len(issues))
        for i, issue in enumerate(issues):
            self.validation_table.setItem(i, 0, QTableWidgetItem(issue.severity.value))
            self.validation_table.setItem(i, 1, QTableWidgetItem(issue.rule))
            self.validation_table.setItem(i, 2, QTableWidgetItem(issue.message))
            val_str = f"{issue.value:.3f}" if issue.value is not None else ""
            if issue.limit is not None:
                val_str += f" / {issue.limit:.3f}"
            self.validation_table.setItem(i, 3, QTableWidgetItem(val_str))

    def _log_result(self) -> None:
        if self._last_result is None:
            return
        lines = [f"Generated: {self._last_result.package.family} (Density {self._last_result.density})"]
        lines.append(f"  Pads: {len(self._last_result.pads)}")
        for note in self._last_result.notes:
            lines.append(f"  {note}")
        if self._last_result.courtyard:
            cy = self._last_result.courtyard
            lines.append(f"  Courtyard: {cy.width:.3f} x {cy.height:.3f} mm")
        self.output_log.setText("\n".join(lines))

    @Slot()
    def _export_footprint(self) -> None:
        if self._last_result is None:
            QMessageBox.warning(self, "No Footprint", "Generate a footprint first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Footprint", "", "KiCad Footprint (*.kicad_mod)")
        if path:
            KiCadModExporter(self._last_result).export(path)
            self.status.showMessage(f"Exported: {path}")

    @Slot()
    def _generate_report(self) -> None:
        if self._last_result is None:
            QMessageBox.warning(self, "No Footprint", "Generate a footprint first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Generate Report", "", "PDF Report (*.pdf)")
        if path:
            PDFReportGenerator(self._last_result).generate(path)
            self.status.showMessage(f"Report: {path}")

    @Slot()
    def _open_library(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Open Library")
        if path:
            self.status.showMessage(f"Library: {path}")

    @Slot()
    def _batch_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Batch Import (CSV)", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            from ..export.batch_import import BatchImporter
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                importer = BatchImporter(tmpdir)
                result = importer.from_csv(path)
            QMessageBox.information(
                self, "Batch Import Complete",
                f"Imported {result.succeeded}/{result.total} footprints.\n"
                f"Failed: {result.failed}"
            )
            self.status.showMessage(f"Batch: {result.succeeded}/{result.total}")
        except Exception as e:
            QMessageBox.critical(self, "Batch Import Error", str(e))

    @Slot()
    def _show_about(self) -> None:
        QMessageBox.about(
            self, "About",
            "KiCad MIL IPC-7351 Footprint Generator v0.1.0\n\n"
            "Open-source IPC-7351C + MIL-grade footprint generator for KiCad.\n"
            "License: GPLv3"
        )
