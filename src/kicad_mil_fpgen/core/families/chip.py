# SPDX-License-Identifier: GPL-3.0-or-later
"""Chip family (resistors, capacitors, inductors)."""

from __future__ import annotations

from typing import ClassVar

from ..constants import (
    CalcType, DensityLevel, FamilyFactors, ChipFactors,
    FAMILY_FACTORS, FAMILY_FACTORS_DEFAULT_DENSITY,
)
from ..ipc7351 import (
    PackageDefinition, PadDimensions, PadPosition, PadShape,
    FootprintResult, FootprintError, ValidationError,
)
from .base import FootprintFamily, FamilyMetadata


class ChipFamily(FootprintFamily):
    """Two-pad chip components: resistors, capacitors, inductors."""

    metadata = FamilyMetadata(
        name="chip",
        aliases=["resistor", "capacitor", "inductor", "rcl"],
        description="Two-pad SMD chip components (resistors, capacitors, inductors)",
        calc_type=CalcType.CHIP,
    )

    @classmethod
    def get_factors(cls, density: str) -> ChipFactors:
        try:
            dl = DensityLevel(density.upper())
        except ValueError:
            dl = DensityLevel.B
        table = FAMILY_FACTORS.get(CalcType.CHIP, {})
        return table.get(dl, table[DensityLevel.B])

    @classmethod
    def calculate(cls, pkg: PackageDefinition, factors: FamilyFactors, result: FootprintResult) -> None:
        if not isinstance(factors, ChipFactors):
            raise FootprintError("Expected ChipFactors for chip family")
        body = pkg.body
        if body is None:
            raise FootprintError("Body dimensions required for chip footprint")

        bl = body.length.nominal
        bw = body.width.nominal
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

        _record(result, "chip_pad_width", "W = B + 2S", bw, f.side, pad_width)
        _record(result, "chip_pad_height", "L = T + H + Toe", bl, f.toe, f.heel, pad_height)
        _record(result, "chip_z_max", "Z = L + 2Toe", bl, f.toe, bl + 2 * f.toe)
        _record(result, "chip_g_min", "G = B - 2S", bw, f.side, bw - 2 * f.side)
        result.notes.append(f"Chip — pad W={pad_width:.3f} H={pad_height:.3f}, 2 pads at ±{pad_center_x:.3f}")


def _record(result: FootprintResult, name: str, formula: str, *args) -> None:
    detail = f"{formula} = {[f'{a:.4f}' if isinstance(a, float) else a for a in args]}"
    result.formulas_used[name] = detail
    result.all_intermediates[name] = {
        "formula": formula,
        "inputs": [float(a) if isinstance(a, (int, float)) else a for a in args],
    }
