# SPDX-License-Identifier: GPL-3.0-or-later
"""Gull-wing family (SOIC, SOT, QFP, QFN, DFN, etc.)."""

from __future__ import annotations

from typing import ClassVar

from ..constants import (
    CalcType, DensityLevel, FamilyFactors, GullwingFactors,
    FAMILY_FACTORS, FAMILY_FACTORS_DEFAULT_DENSITY,
)
from ..ipc7351 import (
    PackageDefinition, PadDimensions, PadPosition, PadShape,
    FootprintResult, FootprintError,
)
from .base import FootprintFamily, FamilyMetadata


class GullwingFamily(FootprintFamily):
    """Gull-wing leaded SMD packages: SOIC, SOT, QFP, QFN, DFN, TSSOP, etc.

    QFN packages optionally include a thermal pad under the body.
    """

    metadata = FamilyMetadata(
        name="gullwing",
        aliases=["soic", "sot", "sod", "tssop", "qfp", "qfn", "dfn", "soj"],
        description="Gull-wing leaded SMD packages",
        requires_leads=True,
        calc_type=CalcType.GULLWING,
    )

    _QFN_FAMILIES = {"qfn", "dfn"}

    @classmethod
    def get_factors(cls, density: str) -> GullwingFactors:
        try:
            dl = DensityLevel(density.upper())
        except ValueError:
            dl = DensityLevel.B
        table = FAMILY_FACTORS.get(CalcType.GULLWING, {})
        return table.get(dl, table[DensityLevel.B])

    @classmethod
    def _is_qfn(cls, pkg: PackageDefinition) -> bool:
        return pkg.family.lower().strip() in cls._QFN_FAMILIES

    @classmethod
    def calculate(cls, pkg: PackageDefinition, factors: FamilyFactors, result: FootprintResult) -> None:
        if not isinstance(factors, GullwingFactors):
            raise FootprintError("Expected GullwingFactors for gullwing family")
        body, leads = pkg.body, pkg.leads
        if body is None or leads is None:
            raise FootprintError("Body and lead dimensions required for gullwing footprint")

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

        if cls._is_qfn(pkg):
            cls._add_thermal_pad(pkg, factors, result, pad_num)

        _record(result, "gullwing_pad_width", "W = LW + 2S", lw, f.side, pad_width)
        _record(result, "gullwing_pad_height", "L = LL + Toe + Heel", ll, f.toe, f.heel, pad_height)
        result.notes.append(f"Gull-wing — {count} leads, pitch={pitch:.3f}, pad W={pad_width:.3f} H={pad_height:.3f}")

    @classmethod
    def _add_thermal_pad(
        cls,
        pkg: PackageDefinition,
        factors: FamilyFactors,
        result: FootprintResult,
        next_pad_num: int,
    ) -> None:
        body = pkg.body
        if body is None:
            return

        thermal_width = body.width.nominal * 0.7
        thermal_height = body.length.nominal * 0.7
        f = factors

        result.pads.append(PadDimensions(
            number=next_pad_num,
            width=thermal_width,
            height=thermal_height,
            toe=f.toe * 0.5,
            heel=f.heel * 0.5,
            side=f.side * 0.5,
            shape=PadShape.ROUNDED_RECTANGLE,
            corner_radius=0.2,
            position=PadPosition(x=0.0, y=0.0),
            notes=["Thermal pad"],
        ))
        result.notes.append(f"  Thermal pad: {thermal_width:.3f} x {thermal_height:.3f} mm")


def _record(result: FootprintResult, name: str, formula: str, *args) -> None:
    detail = f"{formula} = {[f'{a:.4f}' if isinstance(a, float) else a for a in args]}"
    result.formulas_used[name] = detail
    result.all_intermediates[name] = {
        "formula": formula,
        "inputs": [float(a) if isinstance(a, (int, float)) else a for a in args],
    }
