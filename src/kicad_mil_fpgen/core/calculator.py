# SPDX-License-Identifier: GPL-3.0-or-later
"""Calculator wrapper — dispatches to families.calculate with stored defaults."""

from __future__ import annotations

from .ipc7351 import PackageDefinition, FootprintResult
from .families import calculate, apply_mil_derating


class FootprintCalculator:
    """Wrapper for footprint generation with optional stored defaults."""

    def __init__(self, density: str = "B", mil_derating: bool = False):
        self._density = density
        self._mil_derating = mil_derating

    def calculate(self, pkg: PackageDefinition, density: str | None = None) -> FootprintResult:
        density = density or self._density
        result = calculate(pkg, density)
        if self._mil_derating:
            result = apply_mil_derating(result)
        return result

    def apply_mil_derating(self, result: FootprintResult) -> FootprintResult:
        return apply_mil_derating(result)
