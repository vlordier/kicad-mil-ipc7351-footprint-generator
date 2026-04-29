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
    """Ball Grid Array packages: BGA, LGA, CSP."""

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

        pitch = cls._compute_pitch(pkg, ball_d)
        rows, cols = cls._compute_grid(ball_count)
        x_start = -(cols - 1) * pitch / 2
        y_start = -(rows - 1) * pitch / 2

        pad_num = 1
        for row in range(rows):
            for col in range(cols):
                if pad_num > ball_count:
                    break
                x = x_start + col * pitch
                y = y_start + row * pitch
                result.pads.append(PadDimensions(
                    number=pad_num, width=pad_d, height=pad_d,
                    shape=PadShape.CIRCLE,
                    position=PadPosition(x=x, y=y),
                ))
                pad_num += 1

        result.notes.append(f"BGA — {ball_count} balls ({rows}x{cols}), pitch={pitch:.3f}, pad dia={pad_d:.3f}")

    @classmethod
    def _compute_pitch(cls, pkg: PackageDefinition, ball_d: float) -> float:
        if pkg.body is not None and pkg.body.length.nominal > 0 and pkg.body.width.nominal > 0:
            body_area = pkg.body.length.nominal * pkg.body.width.nominal
            if pkg.ball_count > 0:
                pitch = math.sqrt(body_area / pkg.ball_count) * 0.85
                return max(pitch, ball_d * 1.5)
        return ball_d * 1.5

    @classmethod
    def _compute_grid(cls, ball_count: int) -> tuple[int, int]:
        side = int(math.ceil(math.sqrt(ball_count)))
        rows = side
        cols = side
        while rows * cols < ball_count:
            if rows <= cols:
                rows += 1
            else:
                cols += 1
        return rows, cols
