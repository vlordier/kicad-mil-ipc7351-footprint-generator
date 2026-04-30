# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the Tolerance data type."""

from kicad_mil_fpgen.core.tolerances import Tolerance


def test_tolerance_creation():
    t = Tolerance(nominal=1.0, plus=0.1, minus=0.1)
    assert t.nominal == 1.0
    assert t.max_value == 1.1
    assert t.min_value == 0.9


def test_tolerance_symmetric():
    t = Tolerance(nominal=2.0, plus=0.2, minus=0.2)
    assert t.is_symmetric


def test_tolerance_asymmetric():
    t = Tolerance(nominal=2.0, plus=0.3, minus=0.1)
    assert not t.is_symmetric


def test_tolerance_auto_fill():
    """When no tolerance given (0,0), auto-fill to 10% for non-zero nominal."""
    t = Tolerance(nominal=10.0)
    assert t.plus == 1.0
    assert t.minus == 1.0


def test_tolerance_explicit_zero_not_auto_filled():
    """Explicit (0.0, 0.0) tolerance should NOT be auto-filled."""
    t = Tolerance(nominal=1.27, plus=0.0, minus=0.0)
    assert t.plus == 0.0
    assert t.minus == 0.0


def test_tolerance_zero_nominal():
    """Zero nominal should not trigger auto-fill."""
    t = Tolerance(nominal=0.0)
    assert t.plus == 0.0
    assert t.minus == 0.0
