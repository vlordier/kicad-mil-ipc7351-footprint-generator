# SPDX-License-Identifier: GPL-3.0-or-later
"""Data models for IPC-7351B/C footprint generation.

This module defines the core data structures shared across all
package family calculators, exporters, and the CLI layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .tolerances import (
    Tolerance,
    ToleranceStackResult,
)
from .padstack import PadShape
from .constants import (
    CalcType,
    FAMILY_TO_CALC_TYPE,
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class FootprintError(Exception):
    """Raised when footprint calculation fails due to invalid input."""


class ValidationError(FootprintError):
    """Raised when input dimensions fail validation."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class BodyDimensions:
    length: Tolerance
    width: Tolerance
    height: Tolerance
    lead_span: Optional[Tolerance] = None

    def validate(self) -> None:
        if self.length.nominal <= 0:
            raise ValidationError(f"Body length must be positive, got {self.length.nominal}")
        if self.width.nominal <= 0:
            raise ValidationError(f"Body width must be positive, got {self.width.nominal}")
        if self.height.nominal <= 0:
            raise ValidationError(f"Body height must be positive, got {self.height.nominal}")


@dataclass
class LeadDimensions:
    width: Tolerance
    length: Tolerance
    pitch: Tolerance
    count: int = 0
    standoff: Tolerance = field(default_factory=lambda: Tolerance(0.1))

    def validate(self) -> None:
        if self.count < 1:
            raise ValidationError(f"Lead count must be >= 1, got {self.count}")
        if self.pitch.nominal <= 0:
            raise ValidationError(f"Lead pitch must be positive, got {self.pitch.nominal}")
        if self.width.nominal <= 0:
            raise ValidationError(f"Lead width must be positive, got {self.width.nominal}")
        if self.length.nominal <= 0:
            raise ValidationError(f"Lead length must be positive, got {self.length.nominal}")


@dataclass
class PackageDefinition:
    family: str = ""
    body: Optional[BodyDimensions] = None
    leads: Optional[LeadDimensions] = None
    ball_diameter: Optional[Tolerance] = None
    ball_count: int = 0
    pad_to_pad: Optional[Tolerance] = None

    def validate(self) -> None:
        if not self.family:
            raise ValidationError("Package family must not be empty")
        if self.body is None:
            raise ValidationError("Body dimensions are required")
        self.body.validate()
        if self.leads is not None:
            self.leads.validate()
        if self.ball_diameter is not None and self.ball_diameter.nominal <= 0:
            raise ValidationError(f"Ball diameter must be positive, got {self.ball_diameter.nominal}")
        if self.ball_count < 0:
            raise ValidationError(f"Ball count must be non-negative, got {self.ball_count}")

    @property
    def calc_type(self) -> CalcType:
        return FAMILY_TO_CALC_TYPE.get(self.family.lower().strip(), CalcType.CHIP)


@dataclass
class PadPosition:
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0


@dataclass
class PadDimensions:
    number: int = 1
    width: float = 0.0
    height: float = 0.0
    toe: float = 0.0
    heel: float = 0.0
    side: float = 0.0
    shape: PadShape = PadShape.ROUNDED_RECTANGLE
    corner_radius: float = 0.0
    position: PadPosition = field(default_factory=PadPosition)
    notes: list[str] = field(default_factory=list)


@dataclass
class Courtyard:
    """Courtyard dimensions (assembly + silkscreen)."""
    x_min: float = 0.0
    x_max: float = 0.0
    y_min: float = 0.0
    y_max: float = 0.0
    assembly_expansion: float = 0.0
    silkscreen_expansion: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min


@dataclass
class FootprintResult:
    package: Optional[PackageDefinition] = None
    pads: list[PadDimensions] = field(default_factory=list)
    courtyard: Optional[Courtyard] = None
    density: str = "B"
    ipc_version: str = "C"
    tolerance_results: list[ToleranceStackResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    formulas_used: dict[str, str] = field(default_factory=dict)
    all_inputs: dict = field(default_factory=dict)
    all_intermediates: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def body(self) -> Optional[BodyDimensions]:
        if self.package is not None:
            return self.package.body
        return None
