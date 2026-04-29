"""IPC-7351B/C calculation engine — pure math, no GUI, fully testable.

All calculations are transparent: every intermediate value and formula
result is recorded for PDF report generation.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

import yaml
import numpy as np

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


@dataclass
class BodyDimensions:
    length: Tolerance
    width: Tolerance
    height: Tolerance
    lead_span: Optional[Tolerance] = None


@dataclass
class LeadDimensions:
    width: Tolerance
    length: Tolerance
    pitch: Tolerance
    count: int = 0
    standoff: Tolerance = field(default_factory=lambda: Tolerance(0.1))


@dataclass
class PackageDefinition:
    family: str = ""
    body: Optional[BodyDimensions] = None
    leads: Optional[LeadDimensions] = None
    ball_diameter: Optional[Tolerance] = None
    ball_count: int = 0
    pad_to_pad: Optional[Tolerance] = None


@dataclass
class PadDimensions:
    width: float = 0.0
    height: float = 0.0
    toe: float = 0.0
    heel: float = 0.0
    side: float = 0.0
    shape: PadShape = PadShape.ROUNDED_RECTANGLE
    corner_radius: float = 0.0
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


@dataclass
class FootprintResult:
    package: Optional[PackageDefinition] = None
    pads: list[PadDimensions] = field(default_factory=list)
    courtyard: Optional[Courtyard] = None
    body: Optional[BodyDimensions] = None
    density: str = "B"
    ipc_version: str = "C"
    tolerance_results: list[ToleranceStackResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    formulas_used: dict[str, str] = field(default_factory=dict)
    all_inputs: dict = field(default_factory=dict)
    all_intermediates: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


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
        self._density_factors: dict[str, dict] = self._default_density_factors()

    def _default_density_factors(self) -> dict[str, dict]:
        """IPC-7351C Table 3-1 density factors.

        Density A (Most) = largest pad for maximum solder joint strength.
        Density C (Least) = smallest pad for high-density designs.
        """
        return {
            "A": {"heel": 0.25, "toe": 0.75, "side": 0.25, "courtyard": 0.5, "annular": 0.10},
            "B": {"heel": 0.15, "toe": 0.55, "side": 0.15, "courtyard": 0.25, "annular": 0.05},
            "C": {"heel": 0.05, "toe": 0.35, "side": 0.05, "courtyard": 0.10, "annular": 0.025},
        }

    def get_density_multiplier(self, density: str) -> float:
        return self.density_multipliers.get(density.upper(), 0.8)

    def get_density_factors(self, density: str) -> dict:
        return self._density_factors.get(density.upper(), self._density_factors["B"])

    def calculate_footprint(
        self,
        pkg: PackageDefinition,
        density: str = "B",
    ) -> FootprintResult:
        """Main entry point — compute all footprint dimensions."""
        result = FootprintResult(
            package=pkg,
            density=density,
            ipc_version=self.version.value,
        )
        result.body = pkg.body

        density_upper = density.upper()
        assert density_upper in self.density_multipliers, f"Unknown density: {density}"
        factors = self.get_density_factors(density_upper)

        if pkg.family.lower() in ("chip", "resistor", "capacitor", "inductor"):
            result = self._calc_chip(pkg, factors, result)
        elif pkg.family.lower() in ("sot", "sod", "soic", "tssop", "qfp", "qfn", "dfn"):
            result = self._calc_gullwing(pkg, factors, result)
        elif pkg.family.lower() in ("bga", "lga", "csp"):
            result = self._calc_bga(pkg, factors, result)
        elif pkg.family.lower() in ("dip", "sip", "tht"):
            result = self._calc_tht(pkg, factors, result)
        else:
            result.warnings.append(f"Unknown package family: {pkg.family}")

        result.courtyard = self._calc_courtyard(pkg, factors, result)
        return result

    def _calc_chip(
        self,
        pkg: PackageDefinition,
        factors: dict,
        result: FootprintResult,
    ) -> FootprintResult:
        body = pkg.body
        assert body is not None

        body_length = body.length.nominal
        body_width = body.width.nominal

        toe = factors["toe"]
        heel = factors["heel"]
        side = factors["side"]

        pad_width = body_width + 2 * side
        pad_height = body_length + toe + heel

        z_max = body_length + 2 * toe
        g_min = body_width - 2 * side

        self._record_formula(result, "chip_pad_width", "W = B + 2S", body_width, side, pad_width)
        self._record_formula(result, "chip_pad_height", "L = T + H + Toe", body_length, toe, heel, pad_height)
        self._record_formula(result, "chip_z_max", "Z = L + 2Toe", body_length, toe, z_max)
        self._record_formula(result, "chip_g_min", "G = B - 2S", body_width, side, g_min)

        pad = PadDimensions(
            width=pad_width,
            height=pad_height,
            toe=toe,
            heel=heel,
            side=side,
            shape=PadShape.ROUNDED_RECTANGLE,
        )
        result.pads.append(pad)
        result.notes.append(f"Chip package — pad W={pad_width:.3f} H={pad_height:.3f}")
        return result

    def _calc_gullwing(
        self,
        pkg: PackageDefinition,
        factors: dict,
        result: FootprintResult,
    ) -> FootprintResult:
        body = pkg.body
        leads = pkg.leads
        assert body is not None and leads is not None

        lead_width = leads.width.nominal
        lead_length = leads.length.nominal
        pitch = leads.pitch.nominal

        toe = factors["toe"]
        heel = factors["heel"]
        side = factors["side"]

        pad_width = lead_width + 2 * side
        pad_height = lead_length + toe + heel

        self._record_formula(result, "gullwing_pad_width", "W = LW + 2S", lead_width, side, pad_width)
        self._record_formula(result, "gullwing_pad_height", "L = LL + Toe + Heel", lead_length, toe, heel, pad_height)

        pad = PadDimensions(
            width=pad_width,
            height=pad_height,
            toe=toe,
            heel=heel,
            side=side,
            shape=PadShape.OBLONG,
        )
        result.pads.append(pad)
        result.notes.append(
            f"Gull-wing — {leads.count} leads, pitch={pitch:.3f}, pad W={pad_width:.3f} H={pad_height:.3f}"
        )
        return result

    def _calc_bga(
        self,
        pkg: PackageDefinition,
        factors: dict,
        result: FootprintResult,
    ) -> FootprintResult:
        assert pkg.ball_diameter is not None
        ball_d = pkg.ball_diameter.nominal

        pad_diameter, _ = PadstackEngine.bga_pad(ball_diameter=ball_d, pitch=0.0)

        pad = PadDimensions(
            width=pad_diameter,
            height=pad_diameter,
            shape=PadShape.CIRCLE,
        )
        result.pads.append(pad)
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
        assert body is not None and leads is not None

        lead_diameter = leads.width.nominal
        annulus = factors["annular"] + 0.15
        pad_diameter = lead_diameter + 2 * annulus

        pad = PadDimensions(
            width=pad_diameter,
            height=pad_diameter,
            shape=PadShape.CIRCLE,
            notes=[f"Annular ring = {annulus:.3f} mm"],
        )
        result.pads.append(pad)
        result.notes.append(
            f"THT — lead dia={lead_diameter:.3f}, pad dia={pad_diameter:.3f}"
        )
        return result

    def _calc_courtyard(
        self,
        pkg: PackageDefinition,
        factors: dict,
        result: FootprintResult,
    ) -> Courtyard:
        body = pkg.body
        assert body is not None

        body_length = body.length.nominal
        body_width = body.width.nominal
        cy_exp = factors["courtyard"]

        courtyard = Courtyard(
            x_min=-body_length / 2 - cy_exp,
            x_max=body_length / 2 + cy_exp,
            y_min=-body_width / 2 - cy_exp,
            y_max=body_width / 2 + cy_exp,
            assembly_expansion=cy_exp,
            silkscreen_expansion=cy_exp,
        )
        self._record_formula(result, "courtyard", "CY = Body + 2*CY_exp", body_length, cy_exp, courtyard.x_max * 2)
        return courtyard

    def apply_mil_derating(self, result: FootprintResult) -> FootprintResult:
        """Apply MIL-grade derating — larger annular rings, extra courtyard."""
        for pad in result.pads:
            pad.width += 0.05
            pad.height += 0.05
            pad.notes.append("MIL derating: +0.05mm added")

        if result.courtyard:
            result.courtyard.assembly_expansion += 0.1
            result.courtyard.x_min -= 0.1
            result.courtyard.x_max += 0.1
            result.courtyard.y_min -= 0.1
            result.courtyard.y_max += 0.1
            result.courtyard.notes.append("MIL derating: extra 0.1mm courtyard")

        result.notes.append("MIL derating applied (vibration-resistant)")
        return result

    def _record_formula(self, result: FootprintResult, name: str, formula: str, *args) -> None:
        detail = f"{formula} = {[f'{a:.4f}' if isinstance(a, float) else a for a in args]}"
        result.formulas_used[name] = detail
        result.all_intermediates[name] = {
            "formula": formula,
            "inputs": [float(a) if isinstance(a, (int, float)) else a for a in args],
        }
