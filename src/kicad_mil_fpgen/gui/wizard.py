# SPDX-License-Identifier: GPL-3.0-or-later
"""Generation wizard — step-by-step guided footprint creation."""

from PySide6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QDoubleSpinBox,
    QGroupBox,
    QFormLayout,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
)
from PySide6.QtCore import Qt


class PackageSelectionPage(QWizardPage):
    """Step 1: Select package family and basic parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Package Selection")
        self.setSubTitle("Choose the package family and enter basic parameters.")

        layout = QVBoxLayout()
        form = QFormLayout()

        self.family_combo = QComboBox()
        self.family_combo.addItems([
            "Chip (R/C/L)", "SOD", "SOT", "SOIC", "TSSOP",
            "QFP", "QFN", "DFN", "BGA", "LGA", "CSP",
            "DIP", "SIP", "Axial", "Radial", "Connector", "Custom",
        ])
        form.addRow("Package Family:", self.family_combo)

        self.density_combo = QComboBox()
        self.density_combo.addItems(["A (Most — MIL)", "B (Nominal)", "C (Least)", "User", "Manufacturer"])
        form.addRow("Density Level:", self.density_combo)

        self.mil_check = QCheckBox("Enable MIL-Grade Presets")
        self.mil_check.setChecked(True)
        form.addRow(self.mil_check)

        layout.addLayout(form)
        self.setLayout(layout)


class DimensionsPage(QWizardPage):
    """Step 2: Enter body and lead dimensions with tolerances."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Dimensions")
        self.setSubTitle("Enter component body and lead dimensions with tolerances (mm).")

        layout = QVBoxLayout()

        body_group = QGroupBox("Body Dimensions")
        body_form = QFormLayout()
        self.body_length = QDoubleSpinBox()
        self.body_length.setRange(0.1, 200.0)
        self.body_length.setDecimals(3)
        self.body_length.setValue(3.2)
        self.body_length_tol = QDoubleSpinBox()
        self.body_length_tol.setRange(0.0, 10.0)
        self.body_length_tol.setDecimals(3)
        self.body_length_tol.setValue(0.1)
        self.body_width = QDoubleSpinBox()
        self.body_width.setRange(0.1, 200.0)
        self.body_width.setDecimals(3)
        self.body_width.setValue(1.6)
        self.body_width_tol = QDoubleSpinBox()
        self.body_width_tol.setRange(0.0, 10.0)
        self.body_width_tol.setDecimals(3)
        self.body_width_tol.setValue(0.1)
        self.body_height = QDoubleSpinBox()
        self.body_height.setRange(0.01, 50.0)
        self.body_height.setDecimals(3)
        self.body_height.setValue(0.55)
        self.body_height_tol = QDoubleSpinBox()
        self.body_height_tol.setRange(0.0, 10.0)
        self.body_height_tol.setDecimals(3)
        self.body_height_tol.setValue(0.1)

        body_form.addRow("Length (mm):", self.body_length)
        body_form.addRow("Length Tol (±mm):", self.body_length_tol)
        body_form.addRow("Width (mm):", self.body_width)
        body_form.addRow("Width Tol (±mm):", self.body_width_tol)
        body_form.addRow("Height (mm):", self.body_height)
        body_form.addRow("Height Tol (±mm):", self.body_height_tol)
        body_group.setLayout(body_form)

        lead_group = QGroupBox("Lead Dimensions")
        lead_form = QFormLayout()
        self.lead_count = QLineEdit("8")
        self.lead_pitch = QDoubleSpinBox()
        self.lead_pitch.setRange(0.1, 50.0)
        self.lead_pitch.setDecimals(3)
        self.lead_pitch.setValue(1.27)
        self.lead_pitch_tol = QDoubleSpinBox()
        self.lead_pitch_tol.setRange(0.0, 10.0)
        self.lead_pitch_tol.setDecimals(3)
        self.lead_width = QDoubleSpinBox()
        self.lead_width.setRange(0.01, 10.0)
        self.lead_width.setDecimals(3)
        self.lead_width.setValue(0.4)
        self.lead_width_tol = QDoubleSpinBox()
        self.lead_width_tol.setRange(0.0, 10.0)
        self.lead_width_tol.setDecimals(3)
        self.lead_width_tol.setValue(0.05)
        self.lead_length = QDoubleSpinBox()
        self.lead_length.setRange(0.01, 10.0)
        self.lead_length.setDecimals(3)
        self.lead_length.setValue(1.0)
        self.lead_length_tol = QDoubleSpinBox()
        self.lead_length_tol.setRange(0.0, 10.0)
        self.lead_length_tol.setDecimals(3)
        self.lead_length_tol.setValue(0.1)

        lead_form.addRow("Lead Count:", self.lead_count)
        lead_form.addRow("Pitch (mm):", self.lead_pitch)
        lead_form.addRow("Pitch Tol (±mm):", self.lead_pitch_tol)
        lead_form.addRow("Width (mm):", self.lead_width)
        lead_form.addRow("Width Tol (±mm):", self.lead_width_tol)
        lead_form.addRow("Length (mm):", self.lead_length)
        lead_form.addRow("Length Tol (±mm):", self.lead_length_tol)
        lead_group.setLayout(lead_form)

        tol_group = QGroupBox("Tolerance Method")
        tol_layout = QVBoxLayout()
        self.tol_method_group = QButtonGroup(self)
        self.tol_nominal = QRadioButton("Nominal")
        self.tol_minmax = QRadioButton("Min / Max")
        self.tol_rss = QRadioButton("RSS (Statistical)")
        self.tol_worst = QRadioButton("Worst-Case (MIL)")
        self.tol_minmax.setChecked(True)
        self.tol_method_group.addButton(self.tol_nominal)
        self.tol_method_group.addButton(self.tol_minmax)
        self.tol_method_group.addButton(self.tol_rss)
        self.tol_method_group.addButton(self.tol_worst)
        tol_layout.addWidget(self.tol_nominal)
        tol_layout.addWidget(self.tol_minmax)
        tol_layout.addWidget(self.tol_rss)
        tol_layout.addWidget(self.tol_worst)
        tol_group.setLayout(tol_layout)

        layout.addWidget(body_group)
        layout.addWidget(lead_group)
        layout.addWidget(tol_group)
        self.setLayout(layout)


class GenerationWizard(QWizard):
    """Wizard-style interface for guided footprint generation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Footprint")
        self.setMinimumSize(700, 600)

        self.addPage(PackageSelectionPage())
        self.addPage(DimensionsPage())
