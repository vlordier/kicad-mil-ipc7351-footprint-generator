# SPDX-License-Identifier: GPL-3.0-or-later
"""Through-hole family (DIP, SIP, axial, radial)."""

from __future__ import annotations

from typing import ClassVar

from ..constants import (
    CalcType, DensityLevel, FamilyFactors, ThtFactors,
    FAMILY_FACTORS, FAMILY_FACTORS_DEFAULT_DENSITY,
    ANNULAR_RING_BASE,
)
from ..ipc7351 import (
    PackageDefinition, PadDimensions, PadPosition, PadShape,
    FootprintResult, FootprintError,
)
from .base import FootprintFamily, FamilyMetadata


class ThtFamily(FootprintFamily):
    """Through-hole packages: DIP, SIP, axial, radial."""

    metadata = FamilyMetadata(
        name="tht",
        aliases=["dip", "sip", "axial", "radial", "tht", "through-hole"],
        description="Through-hole packages",
        requires_leads=True,
        calc_type=CalcType.THT,
    )

    @classmethod
    def get_factors(cls, density: str) -> ThtFactors:
        try:
            dl = DensityLevel(density.upper())
        except ValueError:
            dl = DensityLevel.B
        table = FAMILY_FACTORS.get(CalcType.THT, {})
        return table.get(dl, table[DensityLevel.B])

    @classmethod
    def calculate(cls, pkg: PackageDefinition, factors: FamilyFactors, result: FootprintResult) -> None:
        if not isinstance(factors, ThtFactors):
            raise FootprintError("Expected ThtFactors for THT family")
        body, leads = pkg.body, pkg.leads
        if body is None or leads is None:
            raise FootprintError("Body and lead dimensions required for THT footprint")

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
