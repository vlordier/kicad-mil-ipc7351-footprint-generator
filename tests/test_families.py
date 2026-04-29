# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for individual family calculator classes."""

import pytest

from kicad_mil_fpgen.core.families.chip import ChipFamily
from kicad_mil_fpgen.core.families.gullwing import GullwingFamily
from kicad_mil_fpgen.core.families.bga import BgaFamily
from kicad_mil_fpgen.core.families.tht import ThtFamily
from kicad_mil_fpgen.core.families.base import FamilyMetadata
from kicad_mil_fpgen.core.ipc7351 import (
    PackageDefinition, BodyDimensions, LeadDimensions, Tolerance,
    FootprintResult, PadShape, ValidationError, FootprintError,
)
from kicad_mil_fpgen.core.constants import (
    ChipFactors, GullwingFactors, BgaFactors, ThtFactors,
    DensityLevel, CalcType,
)


class TestChipFamily:
    def test_metadata(self):
        assert ChipFamily.metadata.name == "chip"
        assert "resistor" in ChipFamily.metadata.aliases
        assert "capacitor" in ChipFamily.metadata.aliases
        assert ChipFamily.metadata.calc_type == CalcType.CHIP

    def test_get_factors_returns_chip_factors(self):
        f = ChipFamily.get_factors("A")
        assert isinstance(f, ChipFactors)
        assert f.toe == 0.60

    def test_get_factors_density_b(self):
        f = ChipFamily.get_factors("B")
        assert f.toe == 0.50

    def test_get_factors_invalid_defaults_to_b(self):
        f = ChipFamily.get_factors("Z")
        assert f.toe == 0.50

    def test_validate_passes(self):
        pkg = PackageDefinition(family="chip", body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)))
        ChipFamily.validate(pkg)

    def test_validate_without_body_raises(self):
        pkg = PackageDefinition(family="chip")
        with pytest.raises(ValidationError):
            ChipFamily.validate(pkg)

    def test_calculate_adds_two_pads(self):
        pkg = PackageDefinition(family="chip", body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)))
        result = FootprintResult(package=pkg)
        ChipFamily.calculate(pkg, ChipFamily.get_factors("B"), result)
        assert len(result.pads) == 2
        assert result.pads[0].shape == PadShape.ROUNDED_RECTANGLE

    def test_calculate_wrong_factors_raises(self):
        from kicad_mil_fpgen.core.constants import BgaFactors
        pkg = PackageDefinition(family="chip", body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)))
        result = FootprintResult(package=pkg)
        wrong_factors = BgaFactors(nsmd_ratio=0.85, smd_ratio=0.90, courtyard=0.25)
        with pytest.raises(FootprintError, match="Expected ChipFactors"):
            ChipFamily.calculate(pkg, wrong_factors, result)


class TestGullwingFamily:
    def test_metadata(self):
        assert GullwingFamily.metadata.name == "gullwing"
        assert "soic" in GullwingFamily.metadata.aliases
        assert "qfp" in GullwingFamily.metadata.aliases
        assert GullwingFamily.metadata.requires_leads is True

    def test_get_factors_returns_gullwing_factors(self):
        f = GullwingFamily.get_factors("A")
        assert isinstance(f, GullwingFactors)

    def test_validate_without_leads_raises(self):
        pkg = PackageDefinition(family="soic", body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)))
        with pytest.raises(ValidationError, match="lead"):
            GullwingFamily.validate(pkg)

    def test_calculate_eight_leads(self):
        pkg = PackageDefinition(family="soic", body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)),
                                leads=LeadDimensions(width=Tolerance(0.4), length=Tolerance(1.0), pitch=Tolerance(1.27), count=8))
        result = FootprintResult(package=pkg)
        GullwingFamily.calculate(pkg, GullwingFamily.get_factors("B"), result)
        assert len(result.pads) == 8


class TestBgaFamily:
    def test_metadata(self):
        assert BgaFamily.metadata.name == "bga"
        assert BgaFamily.metadata.requires_ball is True

    def test_get_factors_returns_bga_factors(self):
        f = BgaFamily.get_factors("B")
        assert isinstance(f, BgaFactors)
        assert f.nsmd_ratio == 0.85

    def test_calculate_single_ball(self):
        pkg = PackageDefinition(family="bga", body=BodyDimensions(length=Tolerance(10.0), width=Tolerance(10.0), height=Tolerance(1.0)),
                                ball_diameter=Tolerance(0.5), ball_count=256)
        result = FootprintResult(package=pkg)
        BgaFamily.calculate(pkg, BgaFamily.get_factors("B"), result)
        assert len(result.pads) == 1
        assert result.pads[0].shape == PadShape.CIRCLE

    def test_calculate_without_ball_raises(self):
        pkg = PackageDefinition(family="bga", body=BodyDimensions(length=Tolerance(10.0), width=Tolerance(10.0), height=Tolerance(1.0)))
        with pytest.raises(FootprintError, match="Ball diameter"):
            result = FootprintResult(package=pkg)
            BgaFamily.calculate(pkg, BgaFamily.get_factors("B"), result)


class TestThtFamily:
    def test_metadata(self):
        assert ThtFamily.metadata.name == "tht"
        assert "dip" in ThtFamily.metadata.aliases

    def test_get_factors_returns_tht_factors(self):
        f = ThtFamily.get_factors("A")
        assert isinstance(f, ThtFactors)
        assert f.annular_extra == 0.15

    def test_calculate_eight_pins(self):
        pkg = PackageDefinition(family="dip", body=BodyDimensions(length=Tolerance(20.0), width=Tolerance(7.0), height=Tolerance(3.5)),
                                leads=LeadDimensions(width=Tolerance(0.6), length=Tolerance(2.0), pitch=Tolerance(2.54), count=8))
        result = FootprintResult(package=pkg)
        ThtFamily.calculate(pkg, ThtFamily.get_factors("B"), result)
        assert len(result.pads) == 8


class TestFamilyConfigTemplate:
    """Every family should provide a YAML config template."""

    def test_chip_template(self):
        t = ChipFamily.get_yaml_config_template()
        assert "aliases" in t
        assert "description" in t

    def test_gullwing_template(self):
        t = GullwingFamily.get_yaml_config_template()
        assert "aliases" in t
