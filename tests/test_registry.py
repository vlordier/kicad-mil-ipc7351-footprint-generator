# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the family registry system."""

import pytest

from kicad_mil_fpgen.core.registry import resolve_family, get_registered_families, get_known_names
from kicad_mil_fpgen.core.families.base import FootprintFamily
from kicad_mil_fpgen.core.families.chip import ChipFamily
from kicad_mil_fpgen.core.families.gullwing import GullwingFamily
from kicad_mil_fpgen.core.families.bga import BgaFamily
from kicad_mil_fpgen.core.families.tht import ThtFamily


class TestResolveFamily:
    """Verify family resolution by name and alias."""

    def test_resolve_chip_by_name(self):
        cls = resolve_family("chip")
        assert cls is ChipFamily

    def test_resolve_chip_by_alias_resistor(self):
        cls = resolve_family("resistor")
        assert cls is ChipFamily

    def test_resolve_chip_by_alias_capacitor(self):
        cls = resolve_family("capacitor")
        assert cls is ChipFamily

    def test_resolve_gullwing_by_name(self):
        cls = resolve_family("gullwing")
        assert cls is GullwingFamily

    def test_resolve_gullwing_by_soic(self):
        cls = resolve_family("soic")
        assert cls is GullwingFamily

    def test_resolve_gullwing_by_qfp(self):
        cls = resolve_family("qfp")
        assert cls is GullwingFamily

    def test_resolve_gullwing_by_tssop(self):
        cls = resolve_family("tssop")
        assert cls is GullwingFamily

    def test_resolve_bga_by_name(self):
        cls = resolve_family("bga")
        assert cls is BgaFamily

    def test_resolve_bga_by_lga(self):
        cls = resolve_family("lga")
        assert cls is BgaFamily

    def test_resolve_tht_by_name(self):
        cls = resolve_family("tht")
        assert cls is ThtFamily

    def test_resolve_tht_by_dip(self):
        cls = resolve_family("dip")
        assert cls is ThtFamily

    def test_resolve_tht_by_axial(self):
        cls = resolve_family("axial")
        assert cls is ThtFamily

    def test_resolve_unknown_returns_none(self):
        assert resolve_family("nonexistent") is None

    def test_resolve_case_insensitive(self):
        cls = resolve_family("SOIC")
        assert cls is GullwingFamily

    def test_resolve_empty_string(self):
        assert resolve_family("") is None


class TestGetRegisteredFamilies:
    """Verify registry contains all built-in families."""

    def test_four_families_registered(self):
        families = get_registered_families()
        assert len(families) >= 4

    def test_all_families_are_footprint_family_subclasses(self):
        for cls in get_registered_families():
            assert issubclass(cls, FootprintFamily)

    def test_known_names_include_all_aliases(self):
        names = get_known_names()
        for alias in ["chip", "resistor", "capacitor", "soic", "qfp", "bga", "dip", "axial"]:
            assert alias in names


class TestCustomFamilyRegistration:
    """Verify that custom families can be registered."""

    def test_custom_family_resolves(self):
        from kicad_mil_fpgen.core.families.base import FamilyMetadata
        from kicad_mil_fpgen.core.constants import CalcType, DensityLevel, FamilyFactors
        from kicad_mil_fpgen.core.ipc7351 import PackageDefinition, FootprintResult

        class CustomConnector(FootprintFamily):
            metadata = FamilyMetadata(
                name="custom_connector",
                aliases=["conn", "header"],
                description="Custom connector family",
                requires_leads=True,
            )

            @classmethod
            def get_factors(cls, density):
                from kicad_mil_fpgen.core.constants import ChipFactors
                return ChipFactors(heel=0.2, toe=0.5, side=0.15, courtyard=0.3)

            @classmethod
            def calculate(cls, pkg, factors, result):
                result.notes.append("Custom connector generated")

        from kicad_mil_fpgen.core.registry import _registry
        _registry.register(CustomConnector)

        cls = resolve_family("custom_connector")
        assert cls is CustomConnector
        cls = resolve_family("conn")
        assert cls is CustomConnector
        cls = resolve_family("header")
        assert cls is CustomConnector
