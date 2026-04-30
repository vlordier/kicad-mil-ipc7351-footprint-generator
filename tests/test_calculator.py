# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the FootprintCalculator wrapper."""

import pytest

from kicad_mil_fpgen.core.calculator import FootprintCalculator
from kicad_mil_fpgen.core.ipc7351 import (
    PackageDefinition, BodyDimensions, Tolerance,
)


class TestFootprintCalculator:
    """Basic instantiation and wrapper behavior — not duplicating calculation tests."""

    def make_chip(self):
        return PackageDefinition(family="chip", body=BodyDimensions(
            length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)))

    def test_default_density(self):
        calc = FootprintCalculator()
        assert calc._density == "B"

    def test_custom_density(self):
        calc = FootprintCalculator(density="A")
        assert calc._density == "A"

    def test_mil_derating_flag(self):
        """mil_derating=True applies derating during calculate()."""
        calc = FootprintCalculator(mil_derating=True)
        result = calc.calculate(self.make_chip())
        assert result.pads[0].width > 0
        assert any("MIL derating" in n for n in result.notes)

    def test_calculate_chip(self):
        calc = FootprintCalculator()
        result = calc.calculate(self.make_chip())
        assert len(result.pads) == 2

    def test_calculate_with_density_override(self):
        calc = FootprintCalculator()
        result = calc.calculate(self.make_chip(), density="A")
        assert result.density == "A"
