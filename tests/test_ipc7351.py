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
    FootprintResult,
    ValidationError,
    FootprintError,
    PadDimensions,
    PadPosition,
    PadShape,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Density / factor lookup tests
# ---------------------------------------------------------------------------

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


def test_get_factors_tht(calc):
    a = calc.get_factors("dip", "A")
    c = calc.get_factors("dip", "C")
    assert a["annular_extra"] > c["annular_extra"]


def test_get_factors_unknown_family_defaults_to_chip(calc):
    f = calc.get_factors("fictitious", "B")
    assert "toe" in f
    assert "side" in f


def test_get_factors_unknown_density_defaults_to_b(calc):
    f = calc.get_factors("chip", "Z")
    assert f["toe"] == 0.50  # density B toe


def test_get_factors_resistor_maps_to_chip(calc):
    f = calc.get_factors("resistor", "A")
    assert f["toe"] == 0.60


def test_get_factors_inductor_maps_to_chip(calc):
    f = calc.get_factors("inductor", "A")
    assert f["toe"] == 0.60


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

def test_calculate_rejects_empty_family(calc):
    pkg = PackageDefinition(family="", body=BodyDimensions(length=Tolerance(1.0), width=Tolerance(1.0), height=Tolerance(0.5)))
    with pytest.raises(ValidationError, match="empty"):
        calc.calculate_footprint(pkg)


def test_calculate_rejects_zero_body_length(calc):
    pkg = PackageDefinition(family="chip", body=BodyDimensions(length=Tolerance(0.0), width=Tolerance(1.0), height=Tolerance(0.5)))
    with pytest.raises(ValidationError, match="positive"):
        calc.calculate_footprint(pkg)


def test_calculate_rejects_zero_body_width(calc):
    pkg = PackageDefinition(family="chip", body=BodyDimensions(length=Tolerance(1.0), width=Tolerance(0.0), height=Tolerance(0.5)))
    with pytest.raises(ValidationError, match="positive"):
        calc.calculate_footprint(pkg)


def test_calculate_rejects_negative_ball_diameter(calc):
    pkg = PackageDefinition(family="bga", body=BodyDimensions(length=Tolerance(10.0), width=Tolerance(10.0), height=Tolerance(1.0)), ball_diameter=Tolerance(-0.5))
    with pytest.raises(ValidationError, match="positive"):
        calc.calculate_footprint(pkg)


def test_calculate_rejects_invalid_density(calc, chip_pkg):
    with pytest.raises(ValidationError, match="density"):
        calc.calculate_footprint(chip_pkg, density="X")


def test_calculate_rejects_negative_ball_count(calc):
    pkg = PackageDefinition(family="bga", body=BodyDimensions(length=Tolerance(10.0), width=Tolerance(10.0), height=Tolerance(1.0)), ball_diameter=Tolerance(0.5), ball_count=-1)
    with pytest.raises(ValidationError, match="non-negative"):
        calc.calculate_footprint(pkg)


def test_calculate_chip_without_body_raises(calc):
    with pytest.raises(ValidationError, match="required"):
        calc.calculate_footprint(PackageDefinition(family="chip"))


# ---------------------------------------------------------------------------
# FootprintResult property tests
# ---------------------------------------------------------------------------

def test_footprint_result_body_property():
    pkg = PackageDefinition(family="chip", body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)))
    result = FootprintResult(package=pkg)
    assert result.body is not None
    assert result.body.length.nominal == 3.2


def test_footprint_result_body_none():
    result = FootprintResult()
    assert result.body is None


# ---------------------------------------------------------------------------
# Courtyard property tests
# ---------------------------------------------------------------------------

def test_courtyard_width_height():
    from kicad_mil_fpgen.core.ipc7351 import Courtyard as CY
    cy = CY(x_min=-3.0, x_max=3.0, y_min=-2.0, y_max=2.0)
    assert cy.width > 0
    assert cy.height > 0


def test_courtyard_properties():
    from kicad_mil_fpgen.core.ipc7351 import Courtyard as CY
    cy = CY(x_min=-3.0, x_max=3.0, y_min=-2.0, y_max=2.0)
    assert cy.width == 6.0
    assert cy.height == 4.0


# ---------------------------------------------------------------------------
# Pad numbering tests
# ---------------------------------------------------------------------------

def test_chip_pad_numbering(calc, chip_pkg):
    result = calc.calculate_footprint(chip_pkg)
    assert result.pads[0].number == 1
    assert result.pads[1].number == 2


def test_gullwing_pad_numbering(calc, gullwing_pkg):
    result = calc.calculate_footprint(gullwing_pkg)
    for i, pad in enumerate(result.pads):
        assert pad.number == i + 1


# ---------------------------------------------------------------------------
# Footprint calculation tests
# ---------------------------------------------------------------------------

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


def test_chip_all_densities(calc, chip_pkg):
    widths = []
    for d in ["A", "B", "C"]:
        r = calc.calculate_footprint(chip_pkg, density=d)
        widths.append(r.pads[0].width)
    assert widths[0] >= widths[1] >= widths[2]


def test_courtyard_based_on_pads(calc, chip_pkg):
    result = calc.calculate_footprint(chip_pkg, density="B")
    cy = result.courtyard
    assert cy.x_min < 0
    assert cy.x_max > 0
    assert cy.y_min < 0
    assert cy.y_max > 0
    # Courtyard must encompass pads
    for pad in result.pads:
        left = pad.position.x - pad.width / 2
        right = pad.position.x + pad.width / 2
        bottom = pad.position.y - pad.height / 2
        top = pad.position.y + pad.height / 2
        assert cy.x_min <= left
        assert cy.x_max >= right
        assert cy.y_min <= bottom
        assert cy.y_max >= top


def test_gullwing_footprint(calc, gullwing_pkg):
    result = calc.calculate_footprint(gullwing_pkg, density="B")
    assert len(result.pads) == 8
    pad = result.pads[0]
    assert pad.width > 0
    assert pad.height > 0
    assert result.courtyard is not None


def test_gullwing_symmetry(calc, gullwing_pkg):
    result = calc.calculate_footprint(gullwing_pkg, density="B")
    # Pairs should be symmetric around origin
    for i in range(0, len(result.pads), 2):
        left = result.pads[i]
        right = result.pads[i + 1]
        assert left.position.x == -right.position.x
        assert left.position.y == right.position.y
        assert left.width == right.width
        assert left.height == right.height


def test_gullwing_count_odd(calc):
    """Odd lead counts should still compute (pads_per_side = count // 2)."""
    pkg = PackageDefinition(
        family="soic",
        body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)),
        leads=LeadDimensions(width=Tolerance(0.4), length=Tolerance(1.0), pitch=Tolerance(1.27), count=7),
    )
    result = calc.calculate_footprint(pkg)
    assert len(result.pads) == 6  # 7 // 2 = 3 per side = 6 total


def test_gullwing_single_lead(calc):
    pkg = PackageDefinition(
        family="soic",
        body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)),
        leads=LeadDimensions(width=Tolerance(0.4), length=Tolerance(1.0), pitch=Tolerance(1.27), count=1),
    )
    result = calc.calculate_footprint(pkg)
    assert len(result.pads) == 0  # 1 // 2 = 0 per side


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


def test_mil_derating_enlarges_courtyard(calc, chip_pkg):
    result = calc.calculate_footprint(chip_pkg, density="B")
    mil_result = calc.apply_mil_derating(result)
    assert mil_result.courtyard.x_max > result.courtyard.x_max
    assert mil_result.courtyard.y_max > result.courtyard.y_max


def test_formulas_recorded(calc, chip_pkg):
    result = calc.calculate_footprint(chip_pkg, density="B")
    assert len(result.formulas_used) >= 4


# ---------------------------------------------------------------------------
# BGA tests
# ---------------------------------------------------------------------------

def test_bga_footprint(calc):
    bga_pkg = PackageDefinition(
        family="bga",
        body=BodyDimensions(length=Tolerance(10.0, 0.1, 0.1), width=Tolerance(10.0, 0.1, 0.1), height=Tolerance(1.2, 0.1, 0.1)),
        ball_diameter=Tolerance(0.5, 0.05, 0.05),
        ball_count=256,
    )
    result = calc.calculate_footprint(bga_pkg, density="B")
    assert len(result.pads) >= 1
    assert result.pads[0].shape == PadShape.CIRCLE


def test_bga_density_scales_pad(calc):
    pkg = PackageDefinition(
        family="bga", body=BodyDimensions(length=Tolerance(10.0), width=Tolerance(10.0), height=Tolerance(1.0)),
        ball_diameter=Tolerance(0.5), ball_count=64,
    )
    r_a = calc.calculate_footprint(pkg, density="A")
    r_c = calc.calculate_footprint(pkg, density="C")
    assert r_a.pads[0].width > r_c.pads[0].width


def test_bga_without_ball_diameter_raises(calc):
    pkg = PackageDefinition(family="bga", body=BodyDimensions(length=Tolerance(10.0), width=Tolerance(10.0), height=Tolerance(1.0)))
    with pytest.raises(FootprintError, match="Ball diameter"):
        calc.calculate_footprint(pkg)


# ---------------------------------------------------------------------------
# THT tests
# ---------------------------------------------------------------------------

def test_tht_footprint(calc):
    tht_pkg = PackageDefinition(
        family="dip",
        body=BodyDimensions(length=Tolerance(20.0, 0.2, 0.2), width=Tolerance(7.0, 0.1, 0.1), height=Tolerance(3.5, 0.1, 0.1)),
        leads=LeadDimensions(width=Tolerance(0.6, 0.05, 0.05), length=Tolerance(2.0, 0.1, 0.1), pitch=Tolerance(2.54, 0.0, 0.0), count=8),
    )
    result = calc.calculate_footprint(tht_pkg, density="B")
    assert len(result.pads) >= 8


def test_tht_pad_annular_ring(calc):
    pkg = PackageDefinition(
        family="dip", body=BodyDimensions(length=Tolerance(20.0), width=Tolerance(7.0), height=Tolerance(3.5)),
        leads=LeadDimensions(width=Tolerance(0.6), length=Tolerance(2.0), pitch=Tolerance(2.54), count=8),
    )
    result = calc.calculate_footprint(pkg, density="A")
    # Density A annular_extra = 0.15, so annulus = 0.15 + 0.15 = 0.30
    expected = 0.6 + 2 * (0.15 + 0.15)
    assert abs(result.pads[0].width - expected) < 0.001


# ---------------------------------------------------------------------------
# Unknown family
# ---------------------------------------------------------------------------

def test_unknown_family_defaults_to_chip(calc):
    """Unknown families now default to chip (no warning)."""
    unknown = PackageDefinition(family="unknown_device", body=BodyDimensions(length=Tolerance(1.0), width=Tolerance(1.0), height=Tolerance(0.5)))
    result = calc.calculate_footprint(unknown, density="B")
    assert len(result.pads) == 2  # treated as chip
    assert len(result.warnings) == 0


# ---------------------------------------------------------------------------
# Courtyard guarantee tests
# ---------------------------------------------------------------------------

def test_courtyard_encompasses_chip_pads(calc, chip_pkg):
    """Courtyard must fully contain all pads with a clearance >= 0."""
    for d in ["A", "B", "C"]:
        result = calc.calculate_footprint(chip_pkg, density=d)
        cy = result.courtyard
        for pad in result.pads:
            assert cy.x_min <= pad.position.x - pad.width / 2
            assert cy.x_max >= pad.position.x + pad.width / 2
            assert cy.y_min <= pad.position.y - pad.height / 2
            assert cy.y_max >= pad.position.y + pad.height / 2


def test_courtyard_encompasses_gullwing_pads(calc, gullwing_pkg):
    result = calc.calculate_footprint(gullwing_pkg, density="B")
    cy = result.courtyard
    for pad in result.pads:
        assert cy.x_min <= pad.position.x - pad.width / 2
        assert cy.x_max >= pad.position.x + pad.width / 2


# ---------------------------------------------------------------------------
# Tolerance integration tests
# ---------------------------------------------------------------------------

def test_tolerance_affects_body_validation():
    """Body tolerance values should be recorded but nominal values drive calculation."""
    bd = BodyDimensions(length=Tolerance(3.2, 0.2, 0.1), width=Tolerance(1.6, 0.15, 0.05), height=Tolerance(0.55, 0.1, 0.1))
    assert bd.length.plus == 0.2
    assert bd.length.minus == 0.1
    assert bd.width.plus == 0.15
    bd.validate()


# ---------------------------------------------------------------------------
# PackageDefinition validate tests
# ---------------------------------------------------------------------------

def test_package_validate_missing_body():
    pkg = PackageDefinition(family="chip")
    with pytest.raises(ValidationError, match="required"):
        pkg.validate()


def test_package_validate_lead_pitch_positive():
    pkg = PackageDefinition(family="soic", body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)),
                            leads=LeadDimensions(width=Tolerance(0.3), length=Tolerance(1.0), pitch=Tolerance(-1.0), count=8))
    with pytest.raises(ValidationError, match="positive"):
        pkg.validate()


def test_package_validate_lead_count_minimum():
    pkg = PackageDefinition(family="soic", body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)),
                            leads=LeadDimensions(width=Tolerance(0.3), length=Tolerance(1.0), pitch=Tolerance(1.27), count=0))
    with pytest.raises(ValidationError, match=">= 1"):
        pkg.validate()


# ---------------------------------------------------------------------------
# Zero / edge cases
# ---------------------------------------------------------------------------

def test_large_body(calc):
    pkg = PackageDefinition(family="chip", body=BodyDimensions(length=Tolerance(200.0), width=Tolerance(150.0), height=Tolerance(20.0)))
    result = calc.calculate_footprint(pkg, density="B")
    assert len(result.pads) == 2
    assert result.pads[0].width > 0


def test_via_family_maps_to_tht(calc):
    """'via' is not in the family map, but 'dip' is."""
    pkg = PackageDefinition(family="axial", body=BodyDimensions(length=Tolerance(10.0), width=Tolerance(3.0), height=Tolerance(3.0)),
                            leads=LeadDimensions(width=Tolerance(0.6), length=Tolerance(2.0), pitch=Tolerance(2.54), count=2))
    result = calc.calculate_footprint(pkg, density="B")
    assert len(result.pads) == 2


def test_radial_maps_to_tht(calc):
    pkg = PackageDefinition(family="radial", body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(5.0), height=Tolerance(10.0)),
                            leads=LeadDimensions(width=Tolerance(0.6), length=Tolerance(2.0), pitch=Tolerance(2.54), count=2))
    result = calc.calculate_footprint(pkg, density="B")
    assert len(result.pads) == 2
