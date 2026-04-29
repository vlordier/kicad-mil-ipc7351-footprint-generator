# SPDX-License-Identifier: GPL-3.0-or-later
"""BGA/LGA/CSP family."""

from __future__ import annotations

from typing import ClassVar

from ..constants import (
    CalcType, DensityLevel, FamilyFactors, BgaFactors,
    FAMILY_FACTORS, FAMILY_FACTORS_DEFAULT_DENSITY,
)
from ..ipc7351 import (
    PackageDefinition, PadDimensions, PadShape,
    FootprintResult, FootprintError,
)
from .base import FootprintFamily, FamilyMetadata


class BgaFamily(FootprintFamily):
    """Ball Grid Array packages: BGA, LGA, CSP."""

    metadata = FamilyMetadata(
        name="bga",
        aliases=["lga", "csp", "bga"],
        description="Ball Grid Array packages",
        requires_ball=True,
        calc_type=CalcType.BGA,
    )

    @classmethod
    def get_factors(cls, density: str) -> BgaFactors:
        try:
            dl = DensityLevel(density.upper())
        except ValueError:
            dl = DensityLevel.B
        table = FAMILY_FACTORS.get(CalcType.BGA, {})
        return table.get(dl, table[DensityLevel.B])

    @classmethod
    def calculate(cls, pkg: PackageDefinition, factors: FamilyFactors, result: FootprintResult) -> None:
        if not isinstance(factors, BgaFactors):
            raise FootprintError("Expected BgaFactors for BGA family")
        if pkg.ball_diameter is None:
            raise FootprintError("Ball diameter required for BGA footprint")

        pad_diameter = pkg.ball_diameter.nominal * factors.nsmd_ratio
        result.pads.append(PadDimensions(
            number=1, width=pad_diameter, height=pad_diameter,
            shape=PadShape.CIRCLE,
        ))
        result.notes.append(f"BGA — {pkg.ball_count} balls, pad dia={pad_diameter:.3f}")
