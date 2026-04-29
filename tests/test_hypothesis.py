# SPDX-License-Identifier: GPL-3.0-or-later
"""Property-based tests using Hypothesis — finds edge cases automatically."""

from hypothesis import given, strategies as st, assume
from hypothesis.extra.numpy import arrays

from kicad_mil_fpgen.core.ipc7351 import (
    IPC7351Calculator,
    PackageDefinition,
    BodyDimensions,
    LeadDimensions,
    Tolerance,
    ValidationError,
    FootprintError,
)

# Valid dimension range (mm)
SMALL = 0.1
MEDIUM = 10.0
LARGE = 200.0


# ---------------------------------------------------------------------------
# Strategy: valid body dimensions for a chip
# ---------------------------------------------------------------------------

positive_floats = st.floats(min_value=SMALL, max_value=LARGE, allow_nan=False, allow_infinity=False)

body_dims = st.builds(
    lambda l, w, h: BodyDimensions(
        length=Tolerance(l, l * 0.05, l * 0.05),
        width=Tolerance(w, w * 0.05, w * 0.05),
        height=Tolerance(h, h * 0.1, h * 0.1),
    ),
    l=positive_floats,
    w=positive_floats,
    h=positive_floats,
)

chip_pkg_strategy = st.builds(
    lambda b: PackageDefinition(family="chip", body=b),
    b=body_dims,
)

lead_dims = st.builds(
    lambda lw, ll, p, c: LeadDimensions(
        width=Tolerance(lw, lw * 0.1, lw * 0.1),
        length=Tolerance(ll, ll * 0.1, ll * 0.1),
        pitch=Tolerance(p, 0.0, 0.0),
        count=c,
    ),
    lw=positive_floats,
    ll=positive_floats,
    p=positive_floats,
    c=st.integers(min_value=2, max_value=128),
)

gullwing_pkg_strategy = st.builds(
    lambda b, l: PackageDefinition(family="soic", body=b, leads=l),
    b=body_dims,
    l=lead_dims,
)


# ===================================================================
# Property: valid chip footprints never crash
# ===================================================================

class TestChipProperties:
    """Property-based tests for chip footprints."""

    calc = IPC7351Calculator()

    @given(pkg=chip_pkg_strategy, density=st.sampled_from(["A", "B", "C"]))
    def test_chip_always_produces_two_pads(self, pkg, density):
        assume(pkg.body is not None)
        assume(pkg.body.length.nominal > 0)
        assume(pkg.body.width.nominal > 0)
        result = self.calc.calculate_footprint(pkg, density=density)
        assert len(result.pads) == 2
        assert result.courtyard is not None

    @given(pkg=chip_pkg_strategy)
    def test_chip_pad_dimensions_positive(self, pkg):
        assume(pkg.body is not None)
        result = self.calc.calculate_footprint(pkg, density="B")
        for pad in result.pads:
            assert pad.width > 0
            assert pad.height > 0
            assert pad.number in (1, 2)

    @given(pkg=chip_pkg_strategy, d1=st.sampled_from(["A", "B", "C"]), d2=st.sampled_from(["A", "B", "C"]))
    def test_chip_monotonic_across_densities(self, pkg, d1, d2):
        assume(pkg.body is not None)
        densities = ["A", "B", "C"]
        assume(densities.index(d1) <= densities.index(d2))
        r1 = self.calc.calculate_footprint(pkg, density=d1)
        r2 = self.calc.calculate_footprint(pkg, density=d2)
        # A >= B >= C
        assert r1.pads[0].width >= r2.pads[0].width - 1e-9


# ===================================================================
# Property: valid gullwing footprints never crash
# ===================================================================

class TestGullwingProperties:
    """Property-based tests for gullwing footprints."""

    calc = IPC7351Calculator()

    @given(pkg=gullwing_pkg_strategy)
    def test_gullwing_pad_count_match(self, pkg):
        assume(pkg.body is not None and pkg.leads is not None)
        assume(pkg.leads.count >= 2)
        result = self.calc.calculate_footprint(pkg, density="B")
        expected = (pkg.leads.count // 2) * 2
        assert len(result.pads) == expected

    @given(pkg=gullwing_pkg_strategy)
    def test_gullwing_pairs_symmetric(self, pkg):
        assume(pkg.body is not None and pkg.leads is not None)
        assume(pkg.leads.count >= 2)
        result = self.calc.calculate_footprint(pkg, density="B")
        for i in range(0, len(result.pads), 2):
            left, right = result.pads[i], result.pads[i + 1]
            assert abs(left.position.x + right.position.x) < 1e-9
            assert left.width == right.width

    @given(pkg=gullwing_pkg_strategy)
    def test_gullwing_pad_dimensions_positive(self, pkg):
        assume(pkg.body is not None and pkg.leads is not None)
        assume(pkg.leads.count >= 2)
        result = self.calc.calculate_footprint(pkg, density="B")
        for pad in result.pads:
            assert pad.width > 0
            assert pad.height > 0


# ===================================================================
# Property: MIL derating preserves structure
# ===================================================================

class TestMILProperties:
    """Property-based tests for MIL derating."""

    calc = IPC7351Calculator()

    @given(pkg=chip_pkg_strategy)
    def test_mil_preserves_pad_count(self, pkg):
        assume(pkg.body is not None)
        result = self.calc.calculate_footprint(pkg, density="B")
        mil = self.calc.apply_mil_derating(result)
        assert len(mil.pads) == len(result.pads)

    @given(pkg=chip_pkg_strategy)
    def test_mil_adds_notes(self, pkg):
        assume(pkg.body is not None)
        result = self.calc.calculate_footprint(pkg, density="B")
        mil = self.calc.apply_mil_derating(result)
        assert any("MIL derating" in n for n in mil.notes)

    @given(pkg=chip_pkg_strategy)
    def test_mil_does_not_mutate_original(self, pkg):
        assume(pkg.body is not None)
        result = self.calc.calculate_footprint(pkg, density="B")
        original_width = result.pads[0].width
        self.calc.apply_mil_derating(result)
        assert result.pads[0].width == original_width


# ===================================================================
# Property: invalid inputs raise properly
# ===================================================================

class TestInvalidInputProperties:
    """Property-based tests for error handling."""

    calc = IPC7351Calculator()

    @given(l=st.floats(max_value=0, allow_nan=False, allow_infinity=False))
    def test_negative_length_raises(self, l):
        assume(l < 0 or l == 0)
        pkg = PackageDefinition(
            family="chip",
            body=BodyDimensions(length=Tolerance(l), width=Tolerance(1.0), height=Tolerance(0.5)),
        )
        with pytest.raises((ValidationError, FootprintError)):
            self.calc.calculate_footprint(pkg)

    @given(c=st.integers(max_value=-1))
    def test_negative_ball_count_raises(self, c):
        pkg = PackageDefinition(
            family="bga",
            body=BodyDimensions(length=Tolerance(10.0), width=Tolerance(10.0), height=Tolerance(1.0)),
            ball_diameter=Tolerance(0.5),
            ball_count=c,
        )
        with pytest.raises(ValidationError):
            self.calc.calculate_footprint(pkg)


import pytest
