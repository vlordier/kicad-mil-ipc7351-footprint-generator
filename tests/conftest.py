# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared fixtures for all tests."""

import pytest

from kicad_mil_fpgen.core.calculator import FootprintCalculator
from kicad_mil_fpgen.core.ipc7351 import (
    PackageDefinition,
    BodyDimensions,
    LeadDimensions,
    Tolerance,
    FootprintResult,
)


# ---------------------------------------------------------------------------
# Calculator fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def calc() -> FootprintCalculator:
    return FootprintCalculator()


# ---------------------------------------------------------------------------
# Package fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def chip_pkg() -> PackageDefinition:
    return PackageDefinition(
        family="chip",
        body=BodyDimensions(
            length=Tolerance(3.2, 0.1, 0.1),
            width=Tolerance(1.6, 0.1, 0.1),
            height=Tolerance(0.55, 0.1, 0.1),
        ),
    )


@pytest.fixture
def gullwing_pkg() -> PackageDefinition:
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


@pytest.fixture
def bga_pkg() -> PackageDefinition:
    return PackageDefinition(
        family="bga",
        body=BodyDimensions(
            length=Tolerance(10.0, 0.1, 0.1),
            width=Tolerance(10.0, 0.1, 0.1),
            height=Tolerance(1.2, 0.1, 0.1),
        ),
        ball_diameter=Tolerance(0.5, 0.05, 0.05),
        ball_count=256,
    )


@pytest.fixture
def tht_pkg() -> PackageDefinition:
    return PackageDefinition(
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


# ---------------------------------------------------------------------------
# Result fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def chip_result(calc, chip_pkg) -> FootprintResult:
    return calc.calculate(chip_pkg, density="B")


@pytest.fixture
def gullwing_result(calc, gullwing_pkg) -> FootprintResult:
    return calc.calculate(gullwing_pkg, density="B")


@pytest.fixture
def bga_result(calc, bga_pkg) -> FootprintResult:
    return calc.calculate(bga_pkg, density="B")


@pytest.fixture
def tht_result(calc, tht_pkg) -> FootprintResult:
    return calc.calculate(tht_pkg, density="B")


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_chip_pkg(length: float = 3.2, width: float = 1.6, height: float = 0.55, tol_pct: float = 5.0) -> PackageDefinition:
    return PackageDefinition(
        family="chip",
        body=BodyDimensions(
            length=Tolerance(length, length * tol_pct / 100, length * tol_pct / 100),
            width=Tolerance(width, width * tol_pct / 100, width * tol_pct / 100),
            height=Tolerance(height, height * tol_pct / 100, height * tol_pct / 100),
        ),
    )


def make_gullwing_pkg(
    length: float = 5.0, width: float = 4.0, height: float = 1.5,
    lead_count: int = 8, pitch: float = 1.27, lead_w: float = 0.4, lead_l: float = 1.0,
) -> PackageDefinition:
    return PackageDefinition(
        family="soic",
        body=BodyDimensions(
            length=Tolerance(length, length * 0.02, length * 0.02),
            width=Tolerance(width, width * 0.025, width * 0.025),
            height=Tolerance(height, height * 0.05, height * 0.05),
        ),
        leads=LeadDimensions(
            width=Tolerance(lead_w, lead_w * 0.1, lead_w * 0.1),
            length=Tolerance(lead_l, lead_l * 0.1, lead_l * 0.1),
            pitch=Tolerance(pitch, 0.0, 0.0),
            count=lead_count,
        ),
    )
