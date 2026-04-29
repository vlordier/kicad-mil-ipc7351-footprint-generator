# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the KiCad export module."""

from kicad_mil_fpgen.core.ipc7351 import (
    IPC7351Calculator,
    PackageDefinition,
    BodyDimensions,
    Tolerance,
)
from kicad_mil_fpgen.export.kicad_mod import KiCadModExporter


def test_kicad_mod_generation():
    calc = IPC7351Calculator(ipc_version="C")
    pkg = PackageDefinition(
        family="chip",
        body=BodyDimensions(
            length=Tolerance(3.2, 0.1, 0.1),
            width=Tolerance(1.6, 0.1, 0.1),
            height=Tolerance(0.55, 0.1, 0.1),
        ),
    )
    result = calc.calculate_footprint(pkg, density="B")
    exporter = KiCadModExporter(result)
    output = exporter.to_string()
    assert "(footprint" in output
    assert "(pad" in output
    assert "(fp_line" in output
    assert "kicad-mil-ipc7351" in output


def test_kicad_mod_has_silkscreen():
    calc = IPC7351Calculator(ipc_version="C")
    pkg = PackageDefinition(
        family="chip",
        body=BodyDimensions(
            length=Tolerance(3.2, 0.1, 0.1),
            width=Tolerance(1.6, 0.1, 0.1),
            height=Tolerance(0.55, 0.1, 0.1),
        ),
    )
    result = calc.calculate_footprint(pkg, density="B")
    exporter = KiCadModExporter(result)
    output = exporter.to_string()
    assert "F.SilkS" in output
    assert "F.CrtYd" in output
