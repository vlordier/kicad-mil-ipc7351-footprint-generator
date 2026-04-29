"""Generation wizard — step-by-step guided footprint creation."""

from PySide6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QDoubleSpinBox,
    QGroupBox,
    QFormLayout,
    QCheckBox,
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
        form.addRow(self.mil_check)

        layout.addLayout(form)
        self.setLayout(layout)


class DimensionsPage(QWizardPage):
    """Step 2: Enter body and lead dimensions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Dimensions")
        self.setSubTitle("Enter component body and lead dimensions (mm).")

        layout = QVBoxLayout()
        body_group = QGroupBox("Body Dimensions")
        body_form = QFormLayout()
        self.body_length = QDoubleSpinBox()
        self.body_length.setRange(0.1, 200.0)
        self.body_length.setDecimals(3)
        self.body_width = QDoubleSpinBox()
        self.body_width.setRange(0.1, 200.0)
        self.body_width.setDecimals(3)
        self.body_height = QDoubleSpinBox()
        self.body_height.setRange(0.01, 50.0)
        self.body_height.setDecimals(3)
        body_form.addRow("Length (mm):", self.body_length)
        body_form.addRow("Width (mm):", self.body_width)
        body_form.addRow("Height (mm):", self.body_height)
        body_group.setLayout(body_form)

        lead_group = QGroupBox("Lead Dimensions")
        lead_form = QFormLayout()
        self.lead_count = QLineEdit()
        self.lead_pitch = QDoubleSpinBox()
        self.lead_pitch.setRange(0.1, 50.0)
        self.lead_pitch.setDecimals(3)
        self.lead_width = QDoubleSpinBox()
        self.lead_width.setRange(0.01, 10.0)
        self.lead_width.setDecimals(3)
        self.lead_length = QDoubleSpinBox()
        self.lead_length.setRange(0.01, 10.0)
        self.lead_length.setDecimals(3)
        lead_form.addRow("Lead Count:", self.lead_count)
        lead_form.addRow("Pitch (mm):", self.lead_pitch)
        lead_form.addRow("Lead Width (mm):", self.lead_width)
        lead_form.addRow("Lead Length (mm):", self.lead_length)
        lead_group.setLayout(lead_form)

        layout.addWidget(body_group)
        layout.addWidget(lead_group)
        self.setLayout(layout)


class GenerationWizard(QWizard):
    """Wizard-style interface for guided footprint generation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Footprint")
        self.setMinimumSize(600, 500)

        self.addPage(PackageSelectionPage())
        self.addPage(DimensionsPage())
