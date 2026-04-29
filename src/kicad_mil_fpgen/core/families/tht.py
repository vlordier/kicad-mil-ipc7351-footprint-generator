# SPDX-License-Identifier: GPL-3.0-or-later
"""Through-hole family (DIP, SIP, axial, radial)."""

from __future__ import annotations

from typing import ClassVar, Optional

from ..constants import (
    CalcType, DensityLevel, FamilyFactors, ThtFactors,
    FAMILY_FACTORS, ANNULAR_RING_BASE,
)
from ..ipc7351 import (
    PackageDefinition, PadDimensions, PadPosition, PadShape,
    FootprintResult, FootprintError,
)
from .base import FootprintFamily, FamilyMetadata


class ThtFamily(FootprintFamily):
    """Through-hole packages: DIP, SIP, axial, radial.

    DIP: dual-row (pads on both sides of body)
    SIP/axial/radial: single-row (pads in a line)
    """

    metadata = FamilyMetadata(
        name="tht",
        aliases=["dip", "sip", "axial", "radial", "tht", "through-hole"],
        description="Through-hole packages",
        requires_leads=True,
        calc_type=CalcType.THT,
    )

    _DUAL_ROW_FAMILIES = {"dip"}

    @classmethod
    def get_factors(cls, density: str) -> ThtFactors:
        try:
            dl = DensityLevel(density.upper())
        except ValueError:
            dl = DensityLevel.B
        table = FAMILY_FACTORS.get(CalcType.THT, {})
        return table.get(dl, table[DensityLevel.B])

    @classmethod
    def _is_dual_row(cls, pkg: PackageDefinition) -> bool:
        return pkg.family.lower().strip() in cls._DUAL_ROW_FAMILIES

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
        pitch = leads.pitch.nominal
        count = leads.count

        if cls._is_dual_row(pkg):
            cls._calc_dual_row(body, leads, pad_d, pitch, count, annulus, result)
        else:
            cls._calc_single_row(body, leads, pad_d, pitch, count, annulus, result)

        result.notes.append(f"THT — lead dia={lead_d:.3f}, pad dia={pad_d:.3f}")

    @classmethod
    def _calc_dual_row(
        cls,
        body,
        leads,
        pad_d: float,
        pitch: float,
        count: int,
        annulus: float,
        result: FootprintResult,
    ) -> None:
        half = count // 2
        body_span = (half - 1) * pitch
        x_left = -(body.length.nominal / 2 + pad_d / 2)
        x_right = body.length.nominal / 2 + pad_d / 2
        pad_num = 1

        for i in range(half):
            y_pos = -body_span / 2 + i * pitch
            result.pads.append(PadDimensions(
                number=pad_num, width=pad_d, height=pad_d,
                shape=PadShape.CIRCLE,
                notes=[f"Annular ring = {annulus:.3f} mm"],
                position=PadPosition(x=x_left, y=y_pos),
            ))
            pad_num += 1

        for i in range(half):
            y_pos = -body_span / 2 + i * pitch
            result.pads.append(PadDimensions(
                number=pad_num, width=pad_d, height=pad_d,
                shape=PadShape.CIRCLE,
                notes=[f"Annular ring = {annulus:.3f} mm"],
                position=PadPosition(x=x_right, y=y_pos),
            ))
            pad_num += 1

    @classmethod
    def _calc_single_row(
        cls,
        body,
        leads,
        pad_d: float,
        pitch: float,
        count: int,
        annulus: float,
        result: FootprintResult,
    ) -> None:
        x_pos = body.length.nominal / 2 + pad_d / 2
        for i in range(count):
            y_pos = -(count - 1) * pitch / 2 + i * pitch
            result.pads.append(PadDimensions(
                number=i + 1, width=pad_d, height=pad_d,
                shape=PadShape.CIRCLE,
                notes=[f"Annular ring = {annulus:.3f} mm"],
                position=PadPosition(x=x_pos, y=y_pos),
            ))
