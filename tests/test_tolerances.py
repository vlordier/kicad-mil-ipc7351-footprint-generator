# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the tolerance calculation engine."""

from kicad_mil_fpgen.core.tolerances import (
    Tolerance,
    ToleranceStack,
    ToleranceEngine,
    ToleranceMethod,
)


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


def test_min_max_stacking():
    t1 = Tolerance(nominal=10.0, plus=0.5, minus=0.5)
    t2 = Tolerance(nominal=5.0, plus=0.2, minus=0.2)
    stack = ToleranceStack(tolerances=[t1, t2], method=ToleranceMethod.MIN_MAX)
    result = stack.compute()
    assert result.nominal == 15.0
    assert result.min == 14.3
    assert result.max == 15.7


def test_rss_stacking():
    t1 = Tolerance(nominal=10.0, plus=1.0, minus=1.0)
    t2 = Tolerance(nominal=5.0, plus=0.5, minus=0.5)
    stack = ToleranceStack(tolerances=[t1, t2], method=ToleranceMethod.RSS)
    result = stack.compute()
    import math
    expected = math.sqrt(1.0**2 + 0.5**2)
    assert abs(result.plus - expected) < 1e-9


def test_solder_fillet():
    toe, heel = ToleranceEngine.solder_fillet(lead_thickness=0.2, pad_length=1.0, class_=3)
    assert toe >= 0.3
    assert heel >= 0.15


def test_empty_stack():
    stack = ToleranceStack(method=ToleranceMethod.NOMINAL)
    result = stack.compute()
    assert result.nominal == 0.0


def test_from_nominal():
    t = ToleranceEngine.from_nominal(10.0, percent=5.0)
    assert t.nominal == 10.0
    assert t.plus == 0.5
    assert t.minus == 0.5
