# SPDX-License-Identifier: GPL-3.0-or-later
"""BGA/LGA/CSP family."""

from __future__ import annotations

import math
from typing import ClassVar

from ..constants import (
    CalcType, DensityLevel, FamilyFactors, BgaFactors,
    FAMILY_FACTORS,
)
from ..ipc7351 import (
    PackageDefinition, PadDimensions, PadPosition, PadShape,
    FootprintResult, FootprintError,
)
from .base import FootprintFamily, FamilyMetadata


class BgaFamily(FootprintFamily):
    """Ball Grid Array packages: BGA, LGA, CSP.

    Computes a rectangular grid from body dimensions and ball count.
    """

    metadata = FamilyMetadata(
        name="bga",
        aliases=["lga", "csp"],
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

        ball_d = pkg.ball_diameter.nominal
        pad_d = ball_d * factors.nsmd_ratio
        ball_count = max(pkg.ball_count, 1)

        pitch_x, pitch_y = cls._compute_pitches(pkg, ball_d)
        rows, cols = cls._compute_grid(ball_count, pkg)
        x_start = -(cols - 1) * pitch_x / 2
        y_start = -(rows - 1) * pitch_y / 2

        pad_num = 1
        for row in range(rows):
            for col in range(cols):
                if pad_num > ball_count:
                    break
                x = x_start + col * pitch_x
                y = y_start + row * pitch_y
                result.pads.append(PadDimensions(
                    number=pad_num, width=pad_d, height=pad_d,
                    shape=PadShape.CIRCLE,
                    position=PadPosition(x=x, y=y),
                ))
                pad_num += 1

        result.notes.append(
            f"BGA — {ball_count} balls ({rows}x{cols}), "
            f"pitch={pitch_x:.3f}x{pitch_y:.3f}, pad dia={pad_d:.3f}"
        )

    @classmethod
    def _compute_pitches(cls, pkg: PackageDefinition, ball_d: float) -> tuple[float, float]:
        if pkg.body is not None and pkg.body.length.nominal > 0 and pkg.body.width.nominal > 0:
            bl = pkg.body.length.nominal
            bw = pkg.body.width.nominal
            if pkg.ball_count > 0:
                pitch_x = math.sqrt((bl * bw) / pkg.ball_count) * 0.85
                pitch_x = max(pitch_x, ball_d * 1.5)
                return pitch_x, pitch_x
        return ball_d * 1.5, ball_d * 1.5

    @classmethod
    def _compute_grid(cls, ball_count: int, pkg: PackageDefinition) -> tuple[int, int]:
        if pkg.body is not None and pkg.body.length.nominal > 0 and pkg.body.width.nominal > 0:
            ratio = pkg.body.length.nominal / pkg.body.width.nominal
            side = int(math.ceil(math.sqrt(ball_count)))
            if ratio > 1.2:
                cols = side
                rows = int(math.ceil(ball_count / cols))
            elif ratio < 0.8:
                rows = side
                cols = int(math.ceil(ball_count / rows))
            else:
                rows = side
                cols = side
            while rows * cols < ball_count:
                if rows <= cols:
                    rows += 1
                else:
                    cols += 1
            return rows, cols
        side = int(math.ceil(math.sqrt(ball_count)))
        return side, side
