# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the high-level FootprintCalculator."""

import pytest

from kicad_mil_fpgen.core.calculator import FootprintCalculator
from kicad_mil_fpgen.core.ipc7351 import (
    PackageDefinition, BodyDimensions, LeadDimensions, Tolerance,
    ValidationError, FootprintError,
)
from kicad_mil_fpgen.config.manager import ConfigManager


class TestFootprintCalculatorBasics:
    """Basic instantiation and profile handling."""

    def test_default_instantiation(self):
        calc = FootprintCalculator()
        assert calc.profile["density"] == "B"
        assert calc.profile["mil_derating"] is False

    def test_profile_mil_standard(self):
        calc = FootprintCalculator(profile="mil_standard")
        assert calc.profile["density"] == "A"
        assert calc.profile["mil_derating"] is True

    def test_profile_nominal(self):
        calc = FootprintCalculator(profile="nominal")
        assert calc.profile["density"] == "B"

    def test_profile_override_density(self):
        calc = FootprintCalculator(profile="mil_standard", density="B")
        assert calc.profile["density"] == "B"
        assert calc.profile["mil_derating"] is True

    def test_override_density(self):
        calc = FootprintCalculator(density="A")
        assert calc.profile["density"] == "A"

    def test_override_mil_derating(self):
        calc = FootprintCalculator(mil_derating=True)
        assert calc.profile["mil_derating"] is True

    def test_invalid_profile_raises(self):
        with pytest.raises(ValueError, match="Unknown profile"):
            FootprintCalculator(profile="nonexistent")


class TestFootprintCalculatorCalculate:
    """Footprint generation via the calculator."""

    def make_chip(self):
        return PackageDefinition(
            family="chip",
            body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)),
        )

    def make_soic8(self):
        return PackageDefinition(
            family="soic",
            body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)),
            leads=LeadDimensions(width=Tolerance(0.4), length=Tolerance(1.0), pitch=Tolerance(1.27), count=8),
        )

    def test_calculate_chip(self):
        calc = FootprintCalculator()
        result = calc.calculate(self.make_chip())
        assert len(result.pads) == 2
        assert result.courtyard is not None

    def test_calculate_chip_density_a(self):
        calc = FootprintCalculator()
        result = calc.calculate(self.make_chip(), density="A")
        assert result.density == "A"

    def test_calculate_soic8(self):
        calc = FootprintCalculator()
        result = calc.calculate(self.make_soic8())
        assert len(result.pads) == 8

    def test_calculate_with_mil_profile_applies_derating(self):
        calc = FootprintCalculator(profile="mil_standard")
        result = calc.calculate(self.make_chip())
        mil = calc.apply_mil_derating(result)
        assert mil.pads[0].width > result.pads[0].width
        assert any("MIL derating" in n for n in mil.notes)

    def test_calculate_unknown_family(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(
            family="unknown",
            body=BodyDimensions(length=Tolerance(1.0), width=Tolerance(1.0), height=Tolerance(0.5)),
        )
        with pytest.raises(ValidationError, match="Unknown package family"):
            calc.calculate(pkg)

    def test_resolve_family_cls(self):
        calc = FootprintCalculator()
        cls = calc.resolve_family_cls("resistor")
        from kicad_mil_fpgen.core.families.chip import ChipFamily
        assert cls is ChipFamily

    def test_resolve_unknown_family_raises(self):
        calc = FootprintCalculator()
        with pytest.raises(ValidationError, match="Unknown package family"):
            calc.resolve_family_cls("nonexistent")


class TestFootprintCalculatorMilDerating:
    """MIL derating via the high-level calculator."""

    def make_chip(self):
        return PackageDefinition(
            family="chip",
            body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)),
        )

    def test_mil_derating_always_applies(self):
        calc = FootprintCalculator(mil_derating=False)
        result = calc.calculate(self.make_chip())
        mil = calc.apply_mil_derating(result)
        # apply_mil_derating always applies derating regardless of profile
        assert mil.pads[0].width == result.pads[0].width + 0.05

    def test_mil_derating_does_not_mutate_original(self):
        calc = FootprintCalculator(mil_derating=True)
        result = calc.calculate(self.make_chip())
        original_width = result.pads[0].width
        calc.apply_mil_derating(result)
        assert result.pads[0].width == original_width


class TestFootprintCalculatorConfig:
    """Integration with ConfigManager."""

    def test_custom_config(self):
        config = ConfigManager()
        calc = FootprintCalculator(config=config, density="C")
        assert calc.profile["density"] == "C"

    def test_profile_via_config(self):
        config = ConfigManager()
        profiles = config.list_profiles()
        assert "mil_standard" in profiles
        assert "nominal" in profiles
        assert "high_density" in profiles

    def test_config_apply_profile(self):
        config = ConfigManager()
        settings = config.apply_profile("mil_standard")
        assert settings["density"] == "A"
        assert settings["mil_derating"] is True
