# SPDX-License-Identifier: GPL-3.0-or-later
"""High-level calculator — orchestrates family registry, config, and export.

Usage:
    calc = FootprintCalculator(profile="mil_standard")
    result = calc.calculate(pkg, density="A")
    calc.apply_mil_derating(result)
    exporter = KiCadModExporter(result)
    exporter.export("my_footprint.kicad_mod")
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Optional, Any

from .families.base import FootprintFamily
from .registry import resolve_family, get_known_names
from .ipc7351 import (
    PackageDefinition, FootprintResult, Courtyard, FootprintError, ValidationError,
)
from .constants import (
    DensityLevel, FamilyFactors, FAMILY_FACTORS, FAMILY_FACTORS_DEFAULT_DENSITY,
    CalcType, MIL_DERATING_PAD_INCREMENT, MIL_DERATING_COURTYARD_INCREMENT,
)
from ..config.manager import ConfigManager, ProfileConfig


class FootprintCalculator:
    """High-level calculator orchestrating family dispatch and configuration."""

    def __init__(
        self,
        profile: Optional[str] = None,
        config: Optional[ConfigManager] = None,
        **kwargs,
    ) -> None:
        self._config = config or ConfigManager()
        self._profile_name = profile
        self._profile_overrides = kwargs

        if profile:
            self._profile = self._config.apply_profile(profile, **kwargs)
        else:
            self._profile = {
                "density": kwargs.get("density", "B"),
                "mil_derating": kwargs.get("mil_derating", False),
                "tolerance_method": kwargs.get("tolerance_method", "min_max"),
                "courtyard_expansion": kwargs.get("courtyard_expansion", 0.25),
                "naming_prefix": kwargs.get("naming_prefix", ""),
                "naming_suffix": kwargs.get("naming_suffix", ""),
                "annular_ring_extra": kwargs.get("annular_ring_extra", 0.0),
                "generate_report": kwargs.get("generate_report", False),
            }

    @property
    def profile(self) -> dict[str, Any]:
        return dict(self._profile)

    def resolve_family_cls(self, family_name: str) -> type[FootprintFamily]:
        cls = resolve_family(family_name)
        if cls is None:
            raise ValidationError(
                f"Unknown package family: '{family_name}'. "
                f"Known: {', '.join(get_known_names())}"
            )
        return cls

    def calculate(
        self,
        pkg: PackageDefinition,
        density: Optional[str] = None,
    ) -> FootprintResult:
        density = density or self._profile["density"]
        pkg.validate()

        family_cls = self.resolve_family_cls(pkg.family)
        family_cls.validate(pkg)

        factors = family_cls.get_factors(density)

        result = FootprintResult(
            package=pkg,
            density=density.upper(),
        )

        family_cls.calculate(pkg, factors, result)
        result.courtyard = self._calc_courtyard(pkg, factors, result, density)
        return result

    def apply_mil_derating(self, result: FootprintResult) -> FootprintResult:
        """Return a copy with MIL-grade derating applied."""
        if not self._profile.get("mil_derating", False):
            return copy.deepcopy(result)

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

    def generate_report(self, result: FootprintResult, output_path: str | Path) -> None:
        if self._profile.get("generate_report", False):
            from ..export.report import PDFReportGenerator
            PDFReportGenerator(result).generate(output_path)

    @staticmethod
    def _calc_courtyard(
        pkg: PackageDefinition,
        factors: FamilyFactors,
        result: FootprintResult,
        density: str,
    ) -> Courtyard:
        cy_exp = getattr(factors, "courtyard", 0.25)

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
            if pkg.body is None:
                raise FootprintError("Cannot compute courtyard: no pads and no body")
            bl, bw = pkg.body.length.nominal, pkg.body.width.nominal
            x_min, x_max = -bl / 2 - cy_exp, bl / 2 + cy_exp
            y_min, y_max = -bw / 2 - cy_exp, bw / 2 + cy_exp

        courtyard = Courtyard(
            x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
            assembly_expansion=cy_exp, silkscreen_expansion=cy_exp,
        )
        result.formulas_used["courtyard"] = f"CY = PadExtent + 2*CY_exp = {x_max - x_min:.4f}"
        return courtyard
