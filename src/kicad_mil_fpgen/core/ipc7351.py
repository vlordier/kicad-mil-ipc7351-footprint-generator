# SPDX-License-Identifier: GPL-3.0-or-later
"""IPC-7351B/C calculation engine — pure math, no GUI, fully testable.

All calculations are transparent: every intermediate value and formula
result is recorded for PDF report generation.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from .tolerances import (
    Tolerance,
    ToleranceStack,
    ToleranceEngine,
    ToleranceMethod,
    ToleranceStackResult,
)
from .padstack import PadstackEngine, PadShape, PadType, PadDefinition, LayerPad


class IPCVersion(Enum):
    B = "B"
    C = "C"


class DensityLevel(Enum):
    A = "A"
    B = "B"
    C = "C"
    USER = "USER"
    MANUFACTURER = "MANUFACTURER"


class FootprintError(Exception):
    """Raised when footprint calculation fails due to invalid input."""


class ValidationError(FootprintError):
    """Raised when input dimensions fail validation."""


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


# ---- Per-family density factors ----
# Values are in mm. Density A (Most) = largest pads for maximum solder joint strength.
# Density C (Least) = smallest pads for high-density designs.
_FAMILY_FACTORS: dict[str, dict[str, dict]] = {
    "chip": {
        "A": {"heel": 0.25, "toe": 0.60, "side": 0.25, "courtyard": 0.50},
        "B": {"heel": 0.20, "toe": 0.50, "side": 0.20, "courtyard": 0.25},
        "C": {"heel": 0.15, "toe": 0.40, "side": 0.15, "courtyard": 0.10},
    },
    "gullwing": {
        "A": {"heel": 0.30, "toe": 0.65, "side": 0.20, "courtyard": 0.50},
        "B": {"heel": 0.25, "toe": 0.55, "side": 0.15, "courtyard": 0.25},
        "C": {"heel": 0.20, "toe": 0.45, "side": 0.10, "courtyard": 0.10},
    },
    "bga": {
        "A": {"nsmd_ratio": 0.90, "smd_ratio": 0.95, "courtyard": 0.50},
        "B": {"nsmd_ratio": 0.85, "smd_ratio": 0.90, "courtyard": 0.25},
        "C": {"nsmd_ratio": 0.80, "smd_ratio": 0.85, "courtyard": 0.10},
    },
    "tht": {
        "A": {"annular_extra": 0.15, "courtyard": 0.50},
        "B": {"annular_extra": 0.10, "courtyard": 0.25},
        "C": {"annular_extra": 0.05, "courtyard": 0.10},
    },
}

_FAMILY_KEY_MAP: dict[str, str] = {
    "chip": "chip", "resistor": "chip", "capacitor": "chip", "inductor": "chip",
    "sot": "gullwing", "sod": "gullwing", "soic": "gullwing", "tssop": "gullwing",
    "qfp": "gullwing", "qfn": "gullwing", "dfn": "gullwing",
    "bga": "bga", "lga": "bga", "csp": "bga",
    "dip": "tht", "sip": "tht", "tht": "tht", "axial": "tht", "radial": "tht",
}

_KICAD_LAYERS_SMD = '"F.Cu" "F.Paste" "F.Mask"'
_KICAD_LAYERS_THT = '"F.Cu" "B.Cu"'


class IPC7351Calculator:
    """Main calculation engine for IPC-7351B/C footprint generation.

    Usage:
        calc = IPC7351Calculator(ipc_version="C")
        result = calc.calculate_footprint(pkg, density="A")
    """

    def __init__(self, ipc_version: str = "C"):
        self.version = IPCVersion(ipc_version.upper())
        self.density_multipliers: dict[str, float] = {
            "A": 1.0,
            "B": 0.8,
            "C": 0.5,
            "USER": 0.75,
            "MANUFACTURER": 0.65,
        }
        self.tolerance_method = ToleranceMethod.MIN_MAX
        self.padstack_engine = PadstackEngine()
        self._family_override: dict | None = None

    def get_density_multiplier(self, density: str) -> float:
        return self.density_multipliers.get(density.upper(), 0.8)

    def get_factors(self, family: str, density: str) -> dict:
        if self._family_override:
            return self._family_override.get(density.upper(), self._family_override.get("B", {}))

        family_lower = family.lower().strip()
        key = _FAMILY_KEY_MAP.get(family_lower, "chip")
        table = _FAMILY_FACTORS.get(key, _FAMILY_FACTORS["chip"])
        return table.get(density.upper(), table["B"])

    def calculate_footprint(
        self,
        pkg: PackageDefinition,
        density: str = "B",
    ) -> FootprintResult:
        """Main entry point — compute all footprint dimensions."""
        pkg.validate()

        density_upper = density.upper()
        if density_upper not in self.density_multipliers:
            raise ValidationError(f"Unknown density level: {density}. Must be one of {list(self.density_multipliers.keys())}")

        result = FootprintResult(
            package=pkg,
            density=density_upper,
            ipc_version=self.version.value,
        )
        factors = self.get_factors(pkg.family, density_upper)

        key = _FAMILY_KEY_MAP.get(pkg.family.lower(), "chip")
        if key == "chip":
            result = self._calc_chip(pkg, factors, result)
        elif key == "gullwing":
            result = self._calc_gullwing(pkg, factors, result)
        elif key == "bga":
            result = self._calc_bga(pkg, factors, result)
        elif key == "tht":
            result = self._calc_tht(pkg, factors, result)
        else:
            result.warnings.append(f"Unknown package family: {pkg.family}")

        result.courtyard = self._calc_courtyard(factors, result)
        return result

    def _calc_chip(
        self,
        pkg: PackageDefinition,
        factors: dict,
        result: FootprintResult,
    ) -> FootprintResult:
        body = pkg.body
        if body is None:
            raise FootprintError("Body dimensions required for chip footprint")
        body.validate()

        body_length = body.length.nominal
        body_width = body.width.nominal

        toe = factors["toe"]
        heel = factors["heel"]
        side = factors["side"]

        pad_width = body_width + 2 * side
        pad_height = body_length + toe + heel

        z_max = body_length + 2 * toe
        g_min = body_width - 2 * side

        pad_center_x = body_length / 2 + (toe - heel) / 2
        result.pads.append(PadDimensions(
            number=1, width=pad_width, height=pad_height,
            toe=toe, heel=heel, side=side,
            shape=PadShape.ROUNDED_RECTANGLE,
            position=PadPosition(x=-pad_center_x, y=0.0),
        ))
        result.pads.append(PadDimensions(
            number=2, width=pad_width, height=pad_height,
            toe=toe, heel=heel, side=side,
            shape=PadShape.ROUNDED_RECTANGLE,
            position=PadPosition(x=pad_center_x, y=0.0),
        ))

        self._record_formula(result, "chip_pad_width", "W = B + 2S", body_width, side, pad_width)
        self._record_formula(result, "chip_pad_height", "L = T + H + Toe", body_length, toe, heel, pad_height)
        self._record_formula(result, "chip_z_max", "Z = L + 2Toe", body_length, toe, z_max)
        self._record_formula(result, "chip_g_min", "G = B - 2S", body_width, side, g_min)

        result.notes.append(f"Chip — pad W={pad_width:.3f} H={pad_height:.3f}, 2 pads at ±{pad_center_x:.3f}")
        return result

    def _calc_gullwing(
        self,
        pkg: PackageDefinition,
        factors: dict,
        result: FootprintResult,
    ) -> FootprintResult:
        body = pkg.body
        leads = pkg.leads
        if body is None or leads is None:
            raise FootprintError("Body and lead dimensions required for gullwing footprint")
        body.validate()
        leads.validate()

        lead_width = leads.width.nominal
        lead_length = leads.length.nominal
        pitch = leads.pitch.nominal
        count = leads.count

        toe = factors["toe"]
        heel = factors["heel"]
        side = factors["side"]

        pad_width = lead_width + 2 * side
        pad_height = lead_length + toe + heel

        self._record_formula(result, "gullwing_pad_width", "W = LW + 2S", lead_width, side, pad_width)
        self._record_formula(result, "gullwing_pad_height", "L = LL + Toe + Heel", lead_length, toe, heel, pad_height)

        pads_per_side = count // 2
        body_span = (pads_per_side - 1) * pitch
        pad_overhang = (pad_height - lead_length) / 2
        pad_num = 1

        for i in range(pads_per_side):
            y_pos = -body_span / 2 + i * pitch
            result.pads.append(PadDimensions(
                number=pad_num, width=pad_width, height=pad_height,
                toe=toe, heel=heel, side=side,
                shape=PadShape.OBLONG,
                position=PadPosition(x=-(body.length.nominal / 2 + pad_overhang), y=y_pos),
            ))
            pad_num += 1
            result.pads.append(PadDimensions(
                number=pad_num, width=pad_width, height=pad_height,
                toe=toe, heel=heel, side=side,
                shape=PadShape.OBLONG,
                position=PadPosition(x=body.length.nominal / 2 + pad_overhang, y=y_pos),
            ))
            pad_num += 1

        result.notes.append(
            f"Gull-wing — {count} leads, pitch={pitch:.3f}, pad W={pad_width:.3f} H={pad_height:.3f}"
        )
        return result

    def _calc_bga(
        self,
        pkg: PackageDefinition,
        factors: dict,
        result: FootprintResult,
    ) -> FootprintResult:
        if pkg.ball_diameter is None:
            raise FootprintError("Ball diameter required for BGA footprint")
        ball_d = pkg.ball_diameter.nominal

        nsmd_ratio = factors.get("nsmd_ratio", 0.85)
        pad_diameter = ball_d * nsmd_ratio

        result.pads.append(PadDimensions(
            number=1, width=pad_diameter, height=pad_diameter,
            shape=PadShape.CIRCLE,
        ))
        result.notes.append(f"BGA — {pkg.ball_count} balls, pad dia={pad_diameter:.3f}")
        return result

    def _calc_tht(
        self,
        pkg: PackageDefinition,
        factors: dict,
        result: FootprintResult,
    ) -> FootprintResult:
        body = pkg.body
        leads = pkg.leads
        if body is None or leads is None:
            raise FootprintError("Body and lead dimensions required for THT footprint")
        body.validate()
        leads.validate()

        lead_diameter = leads.width.nominal
        annulus = factors["annular_extra"] + 0.15
        pad_diameter = lead_diameter + 2 * annulus

        pad_center_x = body.length.nominal / 2 + pad_diameter / 2
        for i in range(leads.count):
            y_pos = -(leads.count - 1) * leads.pitch.nominal / 2 + i * leads.pitch.nominal
            result.pads.append(PadDimensions(
                number=i + 1, width=pad_diameter, height=pad_diameter,
                shape=PadShape.CIRCLE,
                notes=[f"Annular ring = {annulus:.3f} mm"],
                position=PadPosition(x=pad_center_x, y=y_pos),
            ))

        result.notes.append(
            f"THT — lead dia={lead_diameter:.3f}, pad dia={pad_diameter:.3f}"
        )
        return result

    def _calc_courtyard(
        self,
        factors: dict,
        result: FootprintResult,
    ) -> Courtyard:
        """Courtyard based on outermost pad extents + fabrication allowance.

        Per IPC-7351, the courtyard encompasses the land pattern with a
        fabrication clearance applied to the outermost pad edges.
        """
        cy_exp = factors.get("courtyard", 0.25)

        if result.pads:
            xs = []
            ys = []
            for p in result.pads:
                px, py = p.position.x, p.position.y
                xs.extend([px - p.width / 2, px + p.width / 2])
                ys.extend([py - p.height / 2, py + p.height / 2])
            x_min = min(xs) - cy_exp
            x_max = max(xs) + cy_exp
            y_min = min(ys) - cy_exp
            y_max = max(ys) + cy_exp
        else:
            pkg = result.package
            if pkg is None or pkg.body is None:
                raise FootprintError("Cannot compute courtyard: no pads and no body dimensions")
            body = pkg.body
            x_min = -body.length.nominal / 2 - cy_exp
            x_max = body.length.nominal / 2 + cy_exp
            y_min = -body.width.nominal / 2 - cy_exp
            y_max = body.width.nominal / 2 + cy_exp

        courtyard = Courtyard(
            x_min=x_min, x_max=x_max,
            y_min=y_min, y_max=y_max,
            assembly_expansion=cy_exp,
            silkscreen_expansion=cy_exp,
        )
        extent_x = x_max - x_min
        self._record_formula(result, "courtyard", "CY = PadExtent + 2*CY_exp", extent_x, cy_exp, extent_x)
        return courtyard

    def apply_mil_derating(self, result: FootprintResult) -> FootprintResult:
        """Return a copy with MIL-grade derating applied.

        Does NOT mutate the original result.
        """
        mil = copy.deepcopy(result)

        for pad in mil.pads:
            pad.width += 0.05
            pad.height += 0.05
            pad.notes.append("MIL derating: +0.05mm added")

        if mil.courtyard:
            mil.courtyard.assembly_expansion += 0.1
            mil.courtyard.x_min -= 0.1
            mil.courtyard.x_max += 0.1
            mil.courtyard.y_min -= 0.1
            mil.courtyard.y_max += 0.1
            mil.courtyard.notes.append("MIL derating: extra 0.1mm courtyard")

        mil.notes.append("MIL derating applied (vibration-resistant)")
        return mil

    def _record_formula(self, result: FootprintResult, name: str, formula: str, *args) -> None:
        detail = f"{formula} = {[f'{a:.4f}' if isinstance(a, float) else a for a in args]}"
        result.formulas_used[name] = detail
        result.all_intermediates[name] = {
            "formula": formula,
            "inputs": [float(a) if isinstance(a, (int, float)) else a for a in args],
        }
