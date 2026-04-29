# SPDX-License-Identifier: GPL-3.0-or-later
"""IPC-7351B/C calculation engine — pure math, no GUI, fully testable."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Optional

from .tolerances import (
    Tolerance,
    ToleranceStack,
    ToleranceEngine,
    ToleranceMethod,
    ToleranceStackResult,
)
from .padstack import PadShape, PadType, PadDefinition, LayerPad, PadstackEngine
from .constants import (
    CalcType,
    DensityLevel,
    FamilyFactors,
    ChipFactors,
    GullwingFactors,
    BgaFactors,
    ThtFactors,
    FAMILY_TO_CALC_TYPE,
    FAMILY_FACTORS,
    FAMILY_FACTORS_DEFAULT_DENSITY,
    DENSITY_MULTIPLIERS,
    MIL_DERATING_PAD_INCREMENT,
    MIL_DERATING_COURTYARD_INCREMENT,
    ANNULAR_RING_BASE,
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


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

class IPC7351Calculator:
    """Main calculation engine for IPC-7351B/C footprint generation.

    Usage:
        calc = IPC7351Calculator()
        result = calc.calculate_footprint(pkg, density="A")
    """

    def __init__(self) -> None:
        self.tolerance_method = ToleranceMethod.MIN_MAX
        self.padstack_engine = PadstackEngine()

    @staticmethod
    def get_density_multiplier(density: str) -> float:
        try:
            return DENSITY_MULTIPLIERS[DensityLevel(density.upper())]
        except (ValueError, KeyError):
            return 0.8

    @staticmethod
    def get_factors(family: str, density: str) -> FamilyFactors:
        family_lower = family.lower().strip()
        calc_type = FAMILY_TO_CALC_TYPE.get(family_lower, CalcType.CHIP)

        try:
            dl = DensityLevel(density.upper())
        except ValueError:
            dl = DensityLevel.B

        level_table = FAMILY_FACTORS.get(calc_type, FAMILY_FACTORS[CalcType.CHIP])
        return level_table.get(dl, level_table[DensityLevel.B])

    def calculate_footprint(
        self,
        pkg: PackageDefinition,
        density: str = "B",
    ) -> FootprintResult:
        pkg.validate()

        density_upper = density.upper()
        try:
            dl = DensityLevel(density_upper)
        except ValueError:
            raise ValidationError(f"Unknown density level: {density}. Must be one of {[e.value for e in DensityLevel]}")

        if dl not in DENSITY_MULTIPLIERS:
            raise ValidationError(f"Unknown density level: {density}")

        result = FootprintResult(
            package=pkg,
            density=density_upper,
        )
        factors = self.get_factors(pkg.family, density_upper)

        calc_type = pkg.calc_type
        if calc_type == CalcType.CHIP:
            self._calc_chip(pkg, factors, result)
        elif calc_type == CalcType.GULLWING:
            self._calc_gullwing(pkg, factors, result)
        elif calc_type == CalcType.BGA:
            self._calc_bga(pkg, factors, result)
        elif calc_type == CalcType.THT:
            self._calc_tht(pkg, factors, result)

        result.courtyard = self._calc_courtyard(factors, result)
        return result

    def _calc_chip(
        self,
        pkg: PackageDefinition,
        factors: FamilyFactors,
        result: FootprintResult,
    ) -> None:
        if pkg.body is None:
            raise FootprintError("Body dimensions required for chip footprint")
        if not isinstance(factors, ChipFactors):
            raise FootprintError(f"Expected ChipFactors, got {type(factors).__name__}")

        bl = pkg.body.length.nominal
        bw = pkg.body.width.nominal
        f = factors

        pad_width = bw + 2 * f.side
        pad_height = bl + f.toe + f.heel
        pad_center_x = bl / 2 + (f.toe - f.heel) / 2

        result.pads.append(PadDimensions(
            number=1, width=pad_width, height=pad_height,
            toe=f.toe, heel=f.heel, side=f.side,
            shape=PadShape.ROUNDED_RECTANGLE,
            position=PadPosition(x=-pad_center_x, y=0.0),
        ))
        result.pads.append(PadDimensions(
            number=2, width=pad_width, height=pad_height,
            toe=f.toe, heel=f.heel, side=f.side,
            shape=PadShape.ROUNDED_RECTANGLE,
            position=PadPosition(x=pad_center_x, y=0.0),
        ))

        self._record_formula(result, "chip_pad_width", "W = B + 2S", bw, f.side, pad_width)
        self._record_formula(result, "chip_pad_height", "L = T + H + Toe", bl, f.toe, f.heel, pad_height)
        self._record_formula(result, "chip_z_max", "Z = L + 2Toe", bl, f.toe, bl + 2 * f.toe)
        self._record_formula(result, "chip_g_min", "G = B - 2S", bw, f.side, bw - 2 * f.side)
        result.notes.append(f"Chip — pad W={pad_width:.3f} H={pad_height:.3f}, 2 pads at ±{pad_center_x:.3f}")

    def _calc_gullwing(
        self,
        pkg: PackageDefinition,
        factors: FamilyFactors,
        result: FootprintResult,
    ) -> None:
        body, leads = pkg.body, pkg.leads
        if body is None or leads is None:
            raise FootprintError("Body and lead dimensions required for gullwing footprint")
        if not isinstance(factors, GullwingFactors):
            raise FootprintError(f"Expected GullwingFactors, got {type(factors).__name__}")

        f = factors
        lw = leads.width.nominal
        ll = leads.length.nominal
        pitch = leads.pitch.nominal
        count = leads.count

        pad_width = lw + 2 * f.side
        pad_height = ll + f.toe + f.heel
        pads_per_side = count // 2
        body_span = (pads_per_side - 1) * pitch
        pad_overhang = (pad_height - ll) / 2
        pad_num = 1

        for i in range(pads_per_side):
            y_pos = -body_span / 2 + i * pitch
            result.pads.append(PadDimensions(
                number=pad_num, width=pad_width, height=pad_height,
                toe=f.toe, heel=f.heel, side=f.side,
                shape=PadShape.OBLONG,
                position=PadPosition(x=-(body.length.nominal / 2 + pad_overhang), y=y_pos),
            ))
            pad_num += 1
            result.pads.append(PadDimensions(
                number=pad_num, width=pad_width, height=pad_height,
                toe=f.toe, heel=f.heel, side=f.side,
                shape=PadShape.OBLONG,
                position=PadPosition(x=body.length.nominal / 2 + pad_overhang, y=y_pos),
            ))
            pad_num += 1

        self._record_formula(result, "gullwing_pad_width", "W = LW + 2S", lw, f.side, pad_width)
        self._record_formula(result, "gullwing_pad_height", "L = LL + Toe + Heel", ll, f.toe, f.heel, pad_height)
        result.notes.append(f"Gull-wing — {count} leads, pitch={pitch:.3f}, pad W={pad_width:.3f} H={pad_height:.3f}")

    def _calc_bga(
        self,
        pkg: PackageDefinition,
        factors: FamilyFactors,
        result: FootprintResult,
    ) -> None:
        if pkg.ball_diameter is None:
            raise FootprintError("Ball diameter required for BGA footprint")
        if not isinstance(factors, BgaFactors):
            raise FootprintError(f"Expected BgaFactors, got {type(factors).__name__}")

        pad_diameter = pkg.ball_diameter.nominal * factors.nsmd_ratio
        result.pads.append(PadDimensions(
            number=1, width=pad_diameter, height=pad_diameter,
            shape=PadShape.CIRCLE,
        ))
        result.notes.append(f"BGA — {pkg.ball_count} balls, pad dia={pad_diameter:.3f}")

    def _calc_tht(
        self,
        pkg: PackageDefinition,
        factors: FamilyFactors,
        result: FootprintResult,
    ) -> None:
        body, leads = pkg.body, pkg.leads
        if body is None or leads is None:
            raise FootprintError("Body and lead dimensions required for THT footprint")
        if not isinstance(factors, ThtFactors):
            raise FootprintError(f"Expected ThtFactors, got {type(factors).__name__}")

        lead_d = leads.width.nominal
        annulus = factors.annular_extra + ANNULAR_RING_BASE
        pad_d = lead_d + 2 * annulus
        pad_center_x = body.length.nominal / 2 + pad_d / 2

        for i in range(leads.count):
            y_pos = -(leads.count - 1) * leads.pitch.nominal / 2 + i * leads.pitch.nominal
            result.pads.append(PadDimensions(
                number=i + 1, width=pad_d, height=pad_d,
                shape=PadShape.CIRCLE,
                notes=[f"Annular ring = {annulus:.3f} mm"],
                position=PadPosition(x=pad_center_x, y=y_pos),
            ))

        result.notes.append(f"THT — lead dia={lead_d:.3f}, pad dia={pad_d:.3f}")

    @staticmethod
    def _calc_courtyard(
        factors: FamilyFactors,
        result: FootprintResult,
    ) -> Courtyard:
        cy_exp = factors.courtyard if hasattr(factors, 'courtyard') else 0.25

        if result.pads:
            xs, ys = [], []
            for p in result.pads:
                xs.extend([p.position.x - p.width / 2, p.position.x + p.width / 2])
                ys.extend([p.position.y - p.height / 2, p.position.y + p.height / 2])
            x_min = min(xs) - cy_exp
            x_max = max(xs) + cy_exp
            y_min = min(ys) - cy_exp
            y_max = max(ys) + cy_exp
        else:
            pkg = result.package
            if pkg is None or pkg.body is None:
                raise FootprintError("Cannot compute courtyard: no pads and no body dimensions")
            bl = pkg.body.length.nominal
            bw = pkg.body.width.nominal
            x_min, x_max = -bl / 2 - cy_exp, bl / 2 + cy_exp
            y_min, y_max = -bw / 2 - cy_exp, bw / 2 + cy_exp

        courtyard = Courtyard(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
                              assembly_expansion=cy_exp, silkscreen_expansion=cy_exp)
        result.formulas_used["courtyard"] = f"CY = PadExtent + 2*CY_exp = {x_max - x_min:.4f}"
        return courtyard

    @staticmethod
    def apply_mil_derating(result: FootprintResult) -> FootprintResult:
        mil = copy.deepcopy(result)
        inc = MIL_DERATING_PAD_INCREMENT
        cy_inc = MIL_DERATING_COURTYARD_INCREMENT
        for pad in mil.pads:
            pad.width += inc
            pad.height += inc
            pad.notes.append(f"MIL derating: +{inc}mm added")
        if mil.courtyard:
            c = mil.courtyard
            c.assembly_expansion += cy_inc
            c.x_min -= cy_inc
            c.x_max += cy_inc
            c.y_min -= cy_inc
            c.y_max += cy_inc
            c.notes.append(f"MIL derating: extra {cy_inc}mm courtyard")
        mil.notes.append("MIL derating applied (vibration-resistant)")
        return mil

    @staticmethod
    def _record_formula(result: FootprintResult, name: str, formula: str, *args) -> None:
        detail = f"{formula} = {[f'{a:.4f}' if isinstance(a, float) else a for a in args]}"
        result.formulas_used[name] = detail
        result.all_intermediates[name] = {
            "formula": formula,
            "inputs": [float(a) if isinstance(a, (int, float)) else a for a in args],
        }
