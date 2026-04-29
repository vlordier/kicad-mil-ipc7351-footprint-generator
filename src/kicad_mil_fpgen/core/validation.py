# SPDX-License-Identifier: GPL-3.0-or-later
"""IPC-7351C validation system — checks generated footprints against IPC rules.

Validates pad dimensions, courtyard clearances, annular rings, pitch ratios,
and MIL-specific requirements. Generates warnings for violations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .ipc7351 import FootprintResult, PackageDefinition, PadDimensions


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    severity: Severity
    rule: str
    message: str
    value: Optional[float] = None
    limit: Optional[float] = None


class IPCValidator:
    """Validates a FootprintResult against IPC-7351C rules."""

    def __init__(self, result: FootprintResult, ipc_class: int = 3) -> None:
        self.result = result
        self.ipc_class = ipc_class
        self.issues: list[ValidationIssue] = []

    def validate(self) -> list[ValidationIssue]:
        self.issues.clear()
        self._check_pad_dimensions()
        self._check_courtyard()
        self._check_pitch_ratio()
        self._check_annular_ring()
        self._check_mil_requirements()
        return self.issues

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    def _check_pad_dimensions(self) -> None:
        for pad in self.result.pads:
            if pad.width <= 0:
                self.issues.append(ValidationIssue(
                    Severity.ERROR, "IPC-7351-PAD-001",
                    f"Pad {pad.number} has zero or negative width", pad.width,
                ))
            if pad.height <= 0:
                self.issues.append(ValidationIssue(
                    Severity.ERROR, "IPC-7351-PAD-002",
                    f"Pad {pad.number} has zero or negative height", pad.height,
                ))
            if pad.width > 10.0:
                self.issues.append(ValidationIssue(
                    Severity.WARNING, "IPC-7351-PAD-003",
                    f"Pad {pad.number} width {pad.width:.3f}mm exceeds 10mm", pad.width, 10.0,
                ))

    def _check_courtyard(self) -> None:
        cy = self.result.courtyard
        if cy is None:
            self.issues.append(ValidationIssue(
                Severity.ERROR, "IPC-7351-CY-001", "No courtyard defined",
            ))
            return

        pkg = self.result.package
        if pkg is None or pkg.body is None:
            return

        min_clearance = 0.25
        if self.result.density == "A":
            min_clearance = 0.50
        elif self.result.density == "C":
            min_clearance = 0.10

        for pad in self.result.pads:
            pad_left = pad.position.x - pad.width / 2
            pad_right = pad.position.x + pad.width / 2
            pad_bottom = pad.position.y - pad.height / 2
            pad_top = pad.position.y + pad.height / 2

            clearance_x = min(abs(cy.x_min - pad_left), abs(cy.x_max - pad_right))
            clearance_y = min(abs(cy.y_min - pad_bottom), abs(cy.y_max - pad_top))

            if clearance_x < min_clearance - 0.01:
                self.issues.append(ValidationIssue(
                    Severity.WARNING, "IPC-7351-CY-002",
                    f"Courtyard X clearance {clearance_x:.3f}mm below minimum {min_clearance}mm",
                    clearance_x, min_clearance,
                ))
            if clearance_y < min_clearance - 0.01:
                self.issues.append(ValidationIssue(
                    Severity.WARNING, "IPC-7351-CY-003",
                    f"Courtyard Y clearance {clearance_y:.3f}mm below minimum {min_clearance}mm",
                    clearance_y, min_clearance,
                ))

    def _check_pitch_ratio(self) -> None:
        pkg = self.result.package
        if pkg is None or pkg.leads is None:
            return

        pitch = pkg.leads.pitch.nominal
        lead_width = pkg.leads.width.nominal
        ratio = lead_width / pitch if pitch > 0 else 0

        if ratio > 0.6:
            self.issues.append(ValidationIssue(
                Severity.WARNING, "IPC-7351-PR-001",
                f"Lead width/pitch ratio {ratio:.2f} exceeds 0.6 (solder bridging risk)",
                ratio, 0.6,
            ))

    def _check_annular_ring(self) -> None:
        if self.result.package and self.result.package.family.lower() in ("dip", "sip", "tht", "axial", "radial"):
            for pad in self.result.pads:
                min_ring = 0.05 if self.ipc_class >= 3 else 0.025
                if pad.width < 0.6:
                    self.issues.append(ValidationIssue(
                        Severity.WARNING, "IPC-6012-AR-001",
                        f"THT pad {pad.number} diameter {pad.width:.3f}mm may not meet IPC-6012 Class {self.ipc_class}",
                        pad.width, 0.6,
                    ))

    def _check_mil_requirements(self) -> None:
        if "MIL derating" not in " ".join(self.result.notes):
            return

        for pad in self.result.pads:
            if pad.width < 0.5:
                self.issues.append(ValidationIssue(
                    Severity.WARNING, "MIL-PAD-001",
                    f"MIL pad {pad.number} width {pad.width:.3f}mm may be too small for vibration",
                    pad.width, 0.5,
                ))

        cy = self.result.courtyard
        if cy and cy.assembly_expansion < 0.4:
            self.issues.append(ValidationIssue(
                Severity.WARNING, "MIL-CY-001",
                f"MIL courtyard expansion {cy.assembly_expansion:.3f}mm below 0.4mm minimum",
                cy.assembly_expansion, 0.4,
            ))
