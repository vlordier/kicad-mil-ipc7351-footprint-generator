# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared fixtures for all tests."""

import pytest

from kicad_mil_fpgen.core.calculator import FootprintCalculator
from kicad_mil_fpgen.core.ipc7351 import (
    PackageDefinition, BodyDimensions, LeadDimensions, Tolerance, FootprintResult,
)


@pytest.fixture
def calc() -> FootprintCalculator:
    return FootprintCalculator()


@pytest.fixture
def chip_pkg() -> PackageDefinition:
    return PackageDefinition(family="chip", body=BodyDimensions(
        length=Tolerance(3.2, 0.1, 0.1), width=Tolerance(1.6, 0.1, 0.1), height=Tolerance(0.55, 0.1, 0.1)))


@pytest.fixture
def gullwing_pkg() -> PackageDefinition:
    return PackageDefinition(family="soic", body=BodyDimensions(
        length=Tolerance(5.0, 0.1, 0.1), width=Tolerance(4.0, 0.1, 0.1), height=Tolerance(1.5, 0.1, 0.1)),
        leads=LeadDimensions(width=Tolerance(0.4, 0.05, 0.05), length=Tolerance(1.0, 0.1, 0.1),
                             pitch=Tolerance(1.27, 0.0, 0.0), count=8))


@pytest.fixture
def bga_pkg() -> PackageDefinition:
    return PackageDefinition(family="bga", body=BodyDimensions(
        length=Tolerance(10.0, 0.1, 0.1), width=Tolerance(10.0, 0.1, 0.1), height=Tolerance(1.2, 0.1, 0.1)),
        ball_diameter=Tolerance(0.5, 0.05, 0.05), ball_count=256)


@pytest.fixture
def tht_pkg() -> PackageDefinition:
    return PackageDefinition(family="dip", body=BodyDimensions(
        length=Tolerance(20.0, 0.2, 0.2), width=Tolerance(7.0, 0.1, 0.1), height=Tolerance(3.5, 0.1, 0.1)),
        leads=LeadDimensions(width=Tolerance(0.6, 0.05, 0.05), length=Tolerance(2.0, 0.1, 0.1),
                             pitch=Tolerance(2.54, 0.0, 0.0), count=8))


def make_chip_pkg(length=3.2, width=1.6, height=0.55) -> PackageDefinition:
    return PackageDefinition(family="chip", body=BodyDimensions(
        length=Tolerance(length, length * 0.05, length * 0.05),
        width=Tolerance(width, width * 0.05, width * 0.05),
        height=Tolerance(height, height * 0.1, height * 0.1),
    ))


@pytest.fixture
def chip_result(calc, chip_pkg) -> FootprintResult:
    return calc.calculate(chip_pkg)


@pytest.fixture
def gullwing_result(calc, gullwing_pkg) -> FootprintResult:
    return calc.calculate(gullwing_pkg)
