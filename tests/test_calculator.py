# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the FootprintCalculator."""

import pytest

from kicad_mil_fpgen.core.calculator import FootprintCalculator
from kicad_mil_fpgen.core.ipc7351 import (
    PackageDefinition, BodyDimensions, LeadDimensions, Tolerance,
    ValidationError,
)


class TestFootprintCalculator:
    """Basic instantiation and calculation."""

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
        calc = FootprintCalculator(mil_derating=True)
        result = calc.calculate(self.make_chip())
        mil = calc.apply_mil_derating(result)
        assert mil.pads[0].width == result.pads[0].width + 0.05

    def test_calculate_chip(self):
        calc = FootprintCalculator()
        result = calc.calculate(self.make_chip())
        assert len(result.pads) == 2

    def test_calculate_with_density_override(self):
        calc = FootprintCalculator()
        result = calc.calculate(self.make_chip(), density="A")
        assert result.density == "A"

    def test_mil_derating_does_not_mutate(self):
        calc = FootprintCalculator()
        result = calc.calculate(self.make_chip())
        original = result.pads[0].width
        mil = calc.apply_mil_derating(result)
        assert mil.pads[0].width == original + 0.05
        assert result.pads[0].width == original

    def test_mil_derating_adds_notes(self):
        calc = FootprintCalculator()
        result = calc.calculate(self.make_chip())
        mil = calc.apply_mil_derating(result)
        assert any("MIL derating" in n for n in mil.notes)

    def test_unknown_family_defaults_to_chip(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(family="nonexistent", body=BodyDimensions(
            length=Tolerance(1.0), width=Tolerance(1.0), height=Tolerance(0.5)))
        result = calc.calculate(pkg)
        assert len(result.pads) == 2
