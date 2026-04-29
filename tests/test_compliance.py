# SPDX-License-Identifier: GPL-3.0-or-later
"""IPC-7351C compliance verification — non-trivial tests that validate
formulas, symmetry, monotonicity, courtyard correctness, and invariants."""

import math

import pytest

from kicad_mil_fpgen.core.ipc7351 import (
    IPC7351Calculator,
    PackageDefinition,
    BodyDimensions,
    LeadDimensions,
    Tolerance,
    ChipFactors,
    GullwingFactors,
    BgaFactors,
    ThtFactors,
)
from kicad_mil_fpgen.core.constants import (
    FAMILY_FACTORS,
    CalcType,
    DensityLevel,
    MIL_DERATING_PAD_INCREMENT,
)
from .conftest import make_chip_pkg, make_gullwing_pkg


# ===================================================================
# IPC-7351C formula compliance
# ===================================================================

class TestIPC7351Formulas:
    """Verify that pad dimensions exactly match IPC-7351C formulas."""

    def test_chip_pad_width_formula(self, calc):
        """Chip pad_width = body_width + 2*side_expansion."""
        pkg = make_chip_pkg(length=3.2, width=1.6)
        result = calc.calculate_footprint(pkg, density="B")
        f = FAMILY_FACTORS[CalcType.CHIP][DensityLevel.B]
        assert isinstance(f, ChipFactors)
        expected = 1.6 + 2 * f.side
        assert abs(result.pads[0].width - expected) < 1e-9

    def test_chip_pad_height_formula(self, calc):
        """Chip pad_height = body_length + toe + heel."""
        pkg = make_chip_pkg(length=3.2, width=1.6)
        result = calc.calculate_footprint(pkg, density="B")
        f = FAMILY_FACTORS[CalcType.CHIP][DensityLevel.B]
        assert isinstance(f, ChipFactors)
        expected = 3.2 + f.toe + f.heel
        assert abs(result.pads[0].height - expected) < 1e-9

    def test_chip_pad_center_formula(self, calc):
        """Chip pad_center_x = body_length/2 + (toe - heel)/2."""
        pkg = make_chip_pkg(length=3.2, width=1.6)
        result = calc.calculate_footprint(pkg, density="B")
        f = FAMILY_FACTORS[CalcType.CHIP][DensityLevel.B]
        assert isinstance(f, ChipFactors)
        expected = 3.2 / 2 + (f.toe - f.heel) / 2
        assert abs(result.pads[1].position.x - expected) < 1e-9
        assert abs(result.pads[0].position.x + expected) < 1e-9

    def test_gullwing_pad_width_formula(self, calc):
        """Gullwing pad_width = lead_width + 2*side_expansion."""
        pkg = make_gullwing_pkg(lead_w=0.4)
        result = calc.calculate_footprint(pkg, density="B")
        f = FAMILY_FACTORS[CalcType.GULLWING][DensityLevel.B]
        assert isinstance(f, GullwingFactors)
        expected = 0.4 + 2 * f.side
        assert abs(result.pads[0].width - expected) < 1e-9

    def test_gullwing_pad_height_formula(self, calc):
        """Gullwing pad_height = lead_length + toe + heel."""
        pkg = make_gullwing_pkg(lead_l=1.0)
        result = calc.calculate_footprint(pkg, density="B")
        f = FAMILY_FACTORS[CalcType.GULLWING][DensityLevel.B]
        assert isinstance(f, GullwingFactors)
        expected = 1.0 + f.toe + f.heel
        assert abs(result.pads[0].height - expected) < 1e-9

    def test_bga_pad_diameter_formula(self, calc, bga_pkg):
        """BGA pad_diameter = ball_diameter * nsmd_ratio."""
        result = calc.calculate_footprint(bga_pkg, density="B")
        f = FAMILY_FACTORS[CalcType.BGA][DensityLevel.B]
        assert isinstance(f, BgaFactors)
        expected = 0.5 * f.nsmd_ratio
        assert abs(result.pads[0].width - expected) < 1e-9

    def test_tht_pad_diameter_formula(self, calc, tht_pkg):
        """THT pad_diameter = lead_diameter + 2*(annular_extra + base)."""
        from kicad_mil_fpgen.core.constants import ANNULAR_RING_BASE
        result = calc.calculate_footprint(tht_pkg, density="B")
        f = FAMILY_FACTORS[CalcType.THT][DensityLevel.B]
        assert isinstance(f, ThtFactors)
        annulus = f.annular_extra + ANNULAR_RING_BASE
        expected = 0.6 + 2 * annulus
        assert abs(result.pads[0].width - expected) < 1e-9


# ===================================================================
# Monotonicity — density A >= B >= C for all dimensions
# ===================================================================

class TestDensityMonotonicity:
    """All pad dimensions must be monotonically non-increasing A >= B >= C."""

    @staticmethod
    def _check_monotonic(calc, pkg):
        results = {d: calc.calculate_footprint(pkg, density=d) for d in ["A", "B", "C"]}
        for attr in ("width", "height"):
            vals = [results[d].pads[0].__getattribute__(attr) for d in ("A", "B", "C")]
            assert vals[0] >= vals[1] >= vals[2], f"{attr} not monotonic: {vals}"

    def test_chip_width_monotonic(self, calc):
        self._check_monotonic(calc, make_chip_pkg())

    def test_chip_courtyard_monotonic(self, calc):
        results = {d: calc.calculate_footprint(make_chip_pkg(), density=d) for d in ["A", "B", "C"]}
        for side in ("x_max", "y_max"):
            vals = [results[d].courtyard.__getattribute__(side) for d in ("A", "B", "C")]
            assert vals[0] >= vals[1] >= vals[2], f"Courtyard {side} not monotonic: {vals}"

    def test_gullwing_monotonic(self, calc):
        self._check_monotonic(calc, make_gullwing_pkg())

    def test_bga_monotonic(self, calc, bga_pkg):
        self._check_monotonic(calc, bga_pkg)

    def test_tht_monotonic(self, calc, tht_pkg):
        self._check_monotonic(calc, tht_pkg)


# ===================================================================
# Symmetry
# ===================================================================

class TestSymmetry:
    """All footprints must be symmetric about the origin."""

    def test_chip_symmetry(self, calc):
        result = calc.calculate_footprint(make_chip_pkg(), density="B")
        left, right = result.pads[0], result.pads[1]
        assert left.position.x == -right.position.x
        assert left.position.y == right.position.y
        assert left.width == right.width
        assert left.height == right.height

    def test_gullwing_symmetry(self, calc):
        result = calc.calculate_footprint(make_gullwing_pkg(), density="B")
        for i in range(0, len(result.pads), 2):
            left, right = result.pads[i], result.pads[i + 1]
            assert left.position.x == -right.position.x
            assert left.position.y == right.position.y
            assert left.width == right.width

    def test_courtyard_centered(self, calc):
        result = calc.calculate_footprint(make_chip_pkg(), density="B")
        cy = result.courtyard
        assert abs(cy.x_min + cy.x_max) < 1e-9
        assert abs(cy.y_min + cy.y_max) < 1e-9


# ===================================================================
# Courtyard correctness
# ===================================================================

class TestCourtyardCorrectness:
    """Courtyard must fully contain all pads with minimum clearance."""

    def test_courtyard_contains_all_pads(self, calc):
        for _ in range(20):
            bl = 1.0 + abs(hash(str(_))) % 100 / 10
            bw = 0.5 + abs(hash(str(_ + 100))) % 50 / 10
            pkg = make_chip_pkg(length=bl, width=bw)
            for d in ["A", "B", "C"]:
                result = calc.calculate_footprint(pkg, density=d)
                cy = result.courtyard
                for pad in result.pads:
                    left = pad.position.x - pad.width / 2
                    right = pad.position.x + pad.width / 2
                    bottom = pad.position.y - pad.height / 2
                    top = pad.position.y + pad.height / 2
                    assert cy.x_min <= left, f"cy.x_min {cy.x_min} > left {left}"
                    assert cy.x_max >= right, f"cy.x_max {cy.x_max} < right {right}"
                    assert cy.y_min <= bottom
                    assert cy.y_max >= top

    def test_courtyard_clearance_positive(self, calc):
        """Courtyard must extend beyond pads by at least the clearance."""
        pkg = make_chip_pkg()
        result = calc.calculate_footprint(pkg, density="B")
        cy = result.courtyard
        for pad in result.pads:
            dx = min(abs(cy.x_min - (pad.position.x - pad.width / 2)),
                     abs(cy.x_max - (pad.position.x + pad.width / 2)))
            assert dx >= cy.assembly_expansion - 1e-9


# ===================================================================
# MIL derating invariants
# ===================================================================

class TestMilDerating:
    """MIL derating must preserve invariants and apply correct increments."""

    def test_mil_increment_exact(self, calc, chip_pkg):
        result = calc.calculate_footprint(chip_pkg, density="B")
        mil = calc.apply_mil_derating(result)
        for i, pad in enumerate(mil.pads):
            assert abs(pad.width - result.pads[i].width - MIL_DERATING_PAD_INCREMENT) < 1e-9
            assert abs(pad.height - result.pads[i].height - MIL_DERATING_PAD_INCREMENT) < 1e-9

    def test_mil_preserves_symmetry(self, calc, chip_pkg):
        result = calc.calculate_footprint(chip_pkg, density="A")
        mil = calc.apply_mil_derating(result)
        left, right = mil.pads[0], mil.pads[1]
        assert left.position.x == -right.position.x
        assert left.width == right.width

    def test_mil_preserves_formulas(self, calc, chip_pkg):
        result = calc.calculate_footprint(chip_pkg, density="B")
        mil = calc.apply_mil_derating(result)
        assert mil.formulas_used == result.formulas_used

    def test_mil_multiple_calls_independent(self, calc, chip_pkg):
        result = calc.calculate_footprint(chip_pkg, density="B")
        m1 = calc.apply_mil_derating(result)
        m2 = calc.apply_mil_derating(result)
        assert m1.pads[0].width == m2.pads[0].width


# ===================================================================
# Property: pad count invariants
# ===================================================================

class TestPadCountInvariants:
    """Each package family produces a predictable number of pads."""

    def test_chip_always_two(self, calc):
        for bl in [1.0, 3.2, 10.0, 50.0]:
            for bw in [0.5, 1.6, 5.0, 25.0]:
                pkg = make_chip_pkg(length=bl, width=bw)
                for d in ["A", "B", "C"]:
                    r = calc.calculate_footprint(pkg, density=d)
                    assert len(r.pads) == 2

    def test_gullwing_leads_even(self, calc):
        """8-lead SOIC has 8 pads, 14-lead has 14, etc."""
        for count in [8, 14, 16, 20, 24, 28]:
            pkg = make_gullwing_pkg(lead_count=count)
            r = calc.calculate_footprint(pkg, density="B")
            assert len(r.pads) == count

    def test_tht_leads_match(self, calc):
        for count in [4, 8, 16, 24]:
            pkg = PackageDefinition(
                family="dip",
                body=BodyDimensions(length=Tolerance(20.0), width=Tolerance(7.0), height=Tolerance(3.5)),
                leads=LeadDimensions(width=Tolerance(0.6), length=Tolerance(2.0), pitch=Tolerance(2.54), count=count),
            )
            r = calc.calculate_footprint(pkg, density="B")
            assert len(r.pads) == count


# ===================================================================
# Calculator returns identical results for equivalent inputs
# ===================================================================

class TestDeterminism:
    """Same inputs must produce identical outputs."""

    def test_deterministic_chip(self, calc):
        pkg = make_chip_pkg()
        r1 = calc.calculate_footprint(pkg, density="B")
        r2 = calc.calculate_footprint(pkg, density="B")
        for i in range(len(r1.pads)):
            assert r1.pads[i].width == r2.pads[i].width
            assert r1.pads[i].position.x == r2.pads[i].position.x
        assert r1.courtyard.x_min == r2.courtyard.x_min
        assert r1.courtyard.x_max == r2.courtyard.x_max

    def test_deterministic_all_densities(self, calc):
        pkg = make_chip_pkg()
        for d in ["A", "B", "C"]:
            r1 = calc.calculate_footprint(pkg, density=d)
            r2 = calc.calculate_footprint(pkg, density=d)
            assert r1.pads[0].width == r2.pads[0].width


# ===================================================================
# Property: all formulas contain non-empty strings
# ===================================================================

class TestFormulaRecording:
    """Formulas must always be recorded for valid footprints."""

    def test_all_families_record_formulas(self, calc, chip_pkg, gullwing_pkg, bga_pkg, tht_pkg):
        for pkg in [chip_pkg, gullwing_pkg, bga_pkg, tht_pkg]:
            r = calc.calculate_footprint(pkg, density="B")
            # At minimum, courtyard formula is always recorded
            assert "courtyard" in r.formulas_used

    def test_formulas_are_readable(self, calc, chip_pkg):
        r = calc.calculate_footprint(chip_pkg, density="B")
        for name, formula in r.formulas_used.items():
            assert "=" in formula
            assert len(formula) > 5
