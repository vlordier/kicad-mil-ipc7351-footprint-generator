# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the IPC-7351 calculation engine."""

import pytest

from kicad_mil_fpgen.core.ipc7351 import (
    IPC7351Calculator,
    PackageDefinition,
    BodyDimensions,
    LeadDimensions,
    Tolerance,
    DensityLevel,
)


@pytest.fixture
def calc():
    return IPC7351Calculator(ipc_version="C")


@pytest.fixture
def chip_pkg():
    return PackageDefinition(
        family="chip",
        body=BodyDimensions(
            length=Tolerance(3.2, 0.1, 0.1),
            width=Tolerance(1.6, 0.1, 0.1),
            height=Tolerance(0.55, 0.1, 0.1),
        ),
    )


@pytest.fixture
def gullwing_pkg():
    return PackageDefinition(
        family="soic",
        body=BodyDimensions(
            length=Tolerance(5.0, 0.1, 0.1),
            width=Tolerance(4.0, 0.1, 0.1),
            height=Tolerance(1.5, 0.1, 0.1),
        ),
        leads=LeadDimensions(
            width=Tolerance(0.4, 0.05, 0.05),
            length=Tolerance(1.0, 0.1, 0.1),
            pitch=Tolerance(1.27, 0.0, 0.0),
            count=8,
        ),
    )


def test_density_multiplier(calc):
    assert calc.get_density_multiplier("A") == 1.0
    assert calc.get_density_multiplier("B") == 0.8
    assert calc.get_density_multiplier("C") == 0.5


def test_get_factors_chip(calc):
    a = calc.get_factors("chip", "A")
    c = calc.get_factors("chip", "C")
    assert a["toe"] > c["toe"]
    assert a["courtyard"] > c["courtyard"]


def test_get_factors_gullwing(calc):
    a = calc.get_factors("soic", "A")
    c = calc.get_factors("soic", "C")
    assert a["toe"] > c["toe"]


def test_get_factors_bga(calc):
    a = calc.get_factors("bga", "A")
    c = calc.get_factors("bga", "C")
    assert a["nsmd_ratio"] > c["nsmd_ratio"]


def test_chip_footprint(calc, chip_pkg):
    result = calc.calculate_footprint(chip_pkg, density="A")
    assert len(result.pads) == 2
    pad = result.pads[0]
    assert pad.width > 0
    assert pad.height > 0
    assert result.courtyard is not None
    assert len(result.notes) > 0


def test_chip_density_differences(calc, chip_pkg):
    result_a = calc.calculate_footprint(chip_pkg, density="A")
    result_c = calc.calculate_footprint(chip_pkg, density="C")
    assert result_a.pads[0].width > result_c.pads[0].width
    assert result_a.courtyard.x_max > result_c.courtyard.x_max


def test_courtyard_based_on_pads(calc, chip_pkg):
    result = calc.calculate_footprint(chip_pkg, density="B")
    cy = result.courtyard
    assert cy.x_min < 0
    assert cy.x_max > 0
    assert cy.y_min < 0
    assert cy.y_max > 0


def test_gullwing_footprint(calc, gullwing_pkg):
    result = calc.calculate_footprint(gullwing_pkg, density="B")
    assert len(result.pads) == 8
    pad = result.pads[0]
    assert pad.width > 0
    assert pad.height > 0
    assert result.courtyard is not None


def test_mil_derating_does_not_mutate(calc, chip_pkg):
    result = calc.calculate_footprint(chip_pkg, density="B")
    original_width = result.pads[0].width
    mil_result = calc.apply_mil_derating(result)
    assert mil_result.pads[0].width == original_width + 0.05
    assert result.pads[0].width == original_width


def test_mil_derating_adds_notes(calc, chip_pkg):
    result = calc.calculate_footprint(chip_pkg, density="B")
    mil_result = calc.apply_mil_derating(result)
    assert any("MIL derating" in n for n in mil_result.notes)


def test_formulas_recorded(calc, chip_pkg):
    result = calc.calculate_footprint(chip_pkg, density="B")
    assert len(result.formulas_used) > 0


def test_bga_footprint(calc):
    bga_pkg = PackageDefinition(
        family="bga",
        body=BodyDimensions(
            length=Tolerance(10.0, 0.1, 0.1),
            width=Tolerance(10.0, 0.1, 0.1),
            height=Tolerance(1.2, 0.1, 0.1),
        ),
        ball_diameter=Tolerance(0.5, 0.05, 0.05),
        ball_count=256,
    )
    result = calc.calculate_footprint(bga_pkg, density="B")
    assert len(result.pads) >= 1
    assert result.pads[0].shape.name == "CIRCLE"


def test_tht_footprint(calc):
    tht_pkg = PackageDefinition(
        family="dip",
        body=BodyDimensions(
            length=Tolerance(20.0, 0.2, 0.2),
            width=Tolerance(7.0, 0.1, 0.1),
            height=Tolerance(3.5, 0.1, 0.1),
        ),
        leads=LeadDimensions(
            width=Tolerance(0.6, 0.05, 0.05),
            length=Tolerance(2.0, 0.1, 0.1),
            pitch=Tolerance(2.54, 0.0, 0.0),
            count=8,
        ),
    )
    result = calc.calculate_footprint(tht_pkg, density="B")
    assert len(result.pads) >= 1


def test_unknown_family(calc):
    unknown = PackageDefinition(
        family="unknown",
        body=BodyDimensions(
            length=Tolerance(1.0, 0.1, 0.1),
            width=Tolerance(1.0, 0.1, 0.1),
            height=Tolerance(0.5, 0.1, 0.1),
        ),
    )
    result = calc.calculate_footprint(unknown, density="B")
    assert len(result.warnings) > 0


def test_cli_round_trip(calc):
    """End-to-end: generate and export a chip footprint."""
    result = calc.calculate_footprint(chip_pkg_factory(), density="B")
    from kicad_mil_fpgen.export.kicad_mod import KiCadModExporter
    exporter = KiCadModExporter(result)
    output = exporter.to_string()
    assert "(footprint" in output
    assert "(pad" in output
    assert "F.CrtYd" in output
    assert "F.SilkS" in output
    assert "kicad-mil-ipc7351" in output


def chip_pkg_factory():
    return PackageDefinition(
        family="chip",
        body=BodyDimensions(
            length=Tolerance(3.2, 0.1, 0.1),
            width=Tolerance(1.6, 0.1, 0.1),
            height=Tolerance(0.55, 0.1, 0.1),
        ),
    )
