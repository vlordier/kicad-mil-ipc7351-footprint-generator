# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the KiCad export module."""

import re
import tempfile
from pathlib import Path

import pytest

from kicad_mil_fpgen.core.calculator import FootprintCalculator
from kicad_mil_fpgen.core.ipc7351 import (
    PackageDefinition,
    BodyDimensions,
    LeadDimensions,
    Tolerance,
    PadDimensions,
    PadPosition,
    PadShape,
    FootprintResult,
    Courtyard,
)
from kicad_mil_fpgen.export.kicad_mod import KiCadModExporter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def chip_result():
    calc = FootprintCalculator()
    pkg = PackageDefinition(
        family="chip",
        body=BodyDimensions(length=Tolerance(3.2, 0.1, 0.1), width=Tolerance(1.6, 0.1, 0.1), height=Tolerance(0.55, 0.1, 0.1)),
    )
    return calc.calculate(pkg, density="B")


# ---------------------------------------------------------------------------
# Basic export tests
# ---------------------------------------------------------------------------

def test_kicad_mod_generation(chip_result):
    output = KiCadModExporter(chip_result).to_string()
    assert '(footprint' in output
    assert '(pad' in output
    assert '(fp_line' in output
    assert 'kicad-mil-ipc7351' in output


def test_kicad_mod_has_silkscreen(chip_result):
    output = KiCadModExporter(chip_result).to_string()
    assert 'F.SilkS' in output
    assert 'F.CrtYd' in output


def test_kicad_mod_has_all_layers(chip_result):
    output = KiCadModExporter(chip_result).to_string()
    for layer in ['F.Cu', 'F.Paste', 'F.Mask', 'F.CrtYd', 'F.SilkS']:
        assert layer in output


def test_kicad_mod_pad_numbering(chip_result):
    output = KiCadModExporter(chip_result).to_string()
    pads = re.findall(r'\(pad (\d+) smd', output)
    assert pads == ['1', '2']


def test_kicad_mod_footprint_name(chip_result):
    output = KiCadModExporter(chip_result).to_string()
    assert 'chip_3.20x1.60_B' in output


def test_kicad_mod_version(chip_result):
    output = KiCadModExporter(chip_result).to_string()
    assert 'version 20240101' in output


# ---------------------------------------------------------------------------
# Round-trip test
# ---------------------------------------------------------------------------

def test_round_trip_via_file(chip_result):
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test.kicad_mod"
        KiCadModExporter(chip_result).export(out)
        assert out.exists()
        content = out.read_text()
        assert '(footprint "chip_3.20x1.60_B"' in content
        assert content.count('(pad ') == 2
        assert content.count('(fp_line ') == 8  # 4 courtyard + 4 silkscreen


# ---------------------------------------------------------------------------
# Library export test
# ---------------------------------------------------------------------------

def test_write_library(chip_result):
    with tempfile.TemporaryDirectory() as tmpdir:
        exporter = KiCadModExporter(chip_result)
        lib_path = exporter.write_library(tmpdir, "test_lib")
        expected = Path(tmpdir) / "test_lib.pretty"
        assert lib_path == expected
        assert expected.is_dir()
        fps = list(expected.glob("*.kicad_mod"))
        assert len(fps) == 1


# ---------------------------------------------------------------------------
# Edge case: no pads
# ---------------------------------------------------------------------------

def test_export_no_pads():
    result = FootprintResult(package=PackageDefinition(family="empty"))
    output = KiCadModExporter(result).to_string()
    assert '(footprint' in output
    assert '(pad' not in output


def test_export_no_courtyard():
    result = FootprintResult(package=PackageDefinition(family="empty"))
    output = KiCadModExporter(result).to_string()
    assert '(fp_line' not in output


def test_export_no_silkscreen_without_body():
    result = FootprintResult(package=PackageDefinition(family="no_body"))
    output = KiCadModExporter(result).to_string()
    assert 'F.SilkS' not in output


# ---------------------------------------------------------------------------
# Export with courtyard only, no pads
# ---------------------------------------------------------------------------

def test_export_courtyard_no_pads():
    cy = Courtyard(x_min=-5.0, x_max=5.0, y_min=-3.0, y_max=3.0)
    result = FootprintResult(courtyard=cy)
    output = KiCadModExporter(result).to_string()
    assert 'F.CrtYd' in output
    assert '(pad' not in output


# ---------------------------------------------------------------------------
# S-expression validation
# ---------------------------------------------------------------------------

def test_sexp_balanced(chip_result):
    output = KiCadModExporter(chip_result).to_string()
    depth = 0
    in_str = False
    for ch in output:
        if ch == '"':
            in_str = not in_str
        elif ch == '(' and not in_str:
            depth += 1
        elif ch == ')' and not in_str:
            depth -= 1
        assert depth >= 0
    assert depth == 0


# ---------------------------------------------------------------------------
# Pad shape export
# ---------------------------------------------------------------------------

def test_export_circle_pad():
    pad = PadDimensions(number=1, width=0.5, height=0.5, shape=PadShape.CIRCLE)
    result = FootprintResult(pads=[pad])
    output = KiCadModExporter(result).to_string()
    assert 'circle' in output


def test_export_oblong_pad():
    pad = PadDimensions(number=1, width=0.4, height=1.0, shape=PadShape.OBLONG)
    result = FootprintResult(pads=[pad])
    output = KiCadModExporter(result).to_string()
    assert 'roundrect' in output


def test_export_rect_pad():
    pad = PadDimensions(number=1, width=1.0, height=2.0, shape=PadShape.RECTANGLE)
    result = FootprintResult(pads=[pad])
    output = KiCadModExporter(result).to_string()
    assert ' rect ' in output


# ---------------------------------------------------------------------------
# THT layer export
# ---------------------------------------------------------------------------

def test_export_tht_layers():
    pkg = PackageDefinition(
        family="dip",
        body=BodyDimensions(length=Tolerance(20.0), width=Tolerance(7.0), height=Tolerance(3.5)),
        leads=LeadDimensions(width=Tolerance(0.6), length=Tolerance(2.0), pitch=Tolerance(2.54), count=8),
    )
    calc = FootprintCalculator()
    result = calc.calculate(pkg, density="B")
    output = KiCadModExporter(result).to_string()
    # THT should have F.Cu only (no F.Paste/F.Mask)
    for layer in ['F.Paste', 'F.Mask']:
        assert layer not in output


# ---------------------------------------------------------------------------
# Export with all densities
# ---------------------------------------------------------------------------

def test_export_all_densities():
    calc = FootprintCalculator()
    pkg = PackageDefinition(
        family="chip",
        body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)),
    )
    for d in ["A", "B", "C"]:
        result = calc.calculate(pkg, density=d)
        output = KiCadModExporter(result).to_string()
        assert f'_{d}' in output
        assert output.count('(pad ') == 2


# ---------------------------------------------------------------------------
# Multiple pad positions
# ---------------------------------------------------------------------------

def test_export_pad_positions():
    pads = [
        PadDimensions(number=1, width=1.0, height=2.0, position=PadPosition(x=-2.5, y=0.0)),
        PadDimensions(number=2, width=1.0, height=2.0, position=PadPosition(x=2.5, y=0.0)),
    ]
    result = FootprintResult(pads=pads)
    output = KiCadModExporter(result).to_string()
    assert '(at -2.5000 0.0000)' in output
    assert '(at 2.5000 0.0000)' in output
