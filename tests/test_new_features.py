# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for new features: QFN thermal pad, BGA rectangular grid, naming, validation, paste."""

import pytest

from kicad_mil_fpgen.core.calculator import FootprintCalculator
from kicad_mil_fpgen.core.ipc7351 import PackageDefinition, BodyDimensions, LeadDimensions, Tolerance, FootprintResult
from kicad_mil_fpgen.core.naming import NamingConvention
from kicad_mil_fpgen.core.validation import IPCValidator, Severity
from kicad_mil_fpgen.export.kicad_mod import KiCadModExporter


class TestQFNThermalPad:
    """QFN packages should include a thermal pad."""

    def test_qfn_has_thermal_pad(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(
            family="qfn",
            body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(5.0), height=Tolerance(0.8)),
            leads=LeadDimensions(width=Tolerance(0.3), length=Tolerance(0.4), pitch=Tolerance(0.5), count=32),
        )
        result = calc.calculate(pkg, density="B")
        # 32 lead pads + 1 thermal pad
        assert len(result.pads) == 33
        thermal = result.pads[-1]
        assert thermal.notes == ["Thermal pad"]
        assert thermal.position.x == 0.0
        assert thermal.position.y == 0.0

    def test_soic_no_thermal_pad(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(
            family="soic",
            body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)),
            leads=LeadDimensions(width=Tolerance(0.4), length=Tolerance(1.0), pitch=Tolerance(1.27), count=8),
        )
        result = calc.calculate(pkg, density="B")
        assert len(result.pads) == 8

    def test_dfn_has_thermal_pad(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(
            family="dfn",
            body=BodyDimensions(length=Tolerance(3.0), width=Tolerance(3.0), height=Tolerance(0.5)),
            leads=LeadDimensions(width=Tolerance(0.2), length=Tolerance(0.3), pitch=Tolerance(0.4), count=16),
        )
        result = calc.calculate(pkg, density="B")
        assert len(result.pads) == 17


class TestBGARectangularGrid:
    """BGA should compute grid from body dimensions."""

    def test_square_body_square_grid(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(
            family="bga",
            body=BodyDimensions(length=Tolerance(12.0), width=Tolerance(12.0), height=Tolerance(1.0)),
            ball_diameter=Tolerance(0.5), ball_count=256,
        )
        result = calc.calculate(pkg, density="B")
        assert len(result.pads) == 256

    def test_rectangular_body_rectangular_grid(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(
            family="bga",
            body=BodyDimensions(length=Tolerance(15.0), width=Tolerance(10.0), height=Tolerance(1.0)),
            ball_diameter=Tolerance(0.5), ball_count=100,
        )
        result = calc.calculate(pkg, density="B")
        assert len(result.pads) == 100


class TestNamingConvention:
    """Naming convention system."""

    def test_ipc7351_style(self):
        pkg = PackageDefinition(family="soic", body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)))
        result = FootprintResult(package=pkg, density="A")
        n = NamingConvention(style="ipc7351")
        assert n.generate(result) == "soic_5.00x4.00_A"

    def test_mil_style(self):
        pkg = PackageDefinition(family="soic", body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)))
        result = FootprintResult(package=pkg, density="A", ipc_version="C")
        n = NamingConvention(style="mil")
        assert n.generate(result) == "MIL_SOIC_5.00x4.00_A_IPCC"

    def test_custom_prefix_suffix(self):
        pkg = PackageDefinition(family="chip", body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)))
        result = FootprintResult(package=pkg, density="B")
        n = NamingConvention(style="custom", prefix="MIL", suffix="IPC7351C")
        assert n.generate(result) == "MIL_chip_3.2x1.6_B_IPC7351C"

    def test_no_package(self):
        result = FootprintResult()
        n = NamingConvention()
        assert n.generate(result) == "unnamed_footprint"


class TestIPCValidator:
    """IPC validation system."""

    def test_valid_footprint(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(family="chip", body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)))
        result = calc.calculate(pkg, density="B")
        v = IPCValidator(result)
        issues = v.validate()
        assert v.is_valid

    def test_no_courtyard_fails(self):
        result = FootprintResult(package=PackageDefinition(family="chip"))
        v = IPCValidator(result)
        issues = v.validate()
        assert not v.is_valid
        assert any(i.rule == "IPC-7351-CY-001" for i in issues)

    def test_mil_warnings(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(family="chip", body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)))
        result = calc.calculate(pkg, density="B")
        result = calc.apply_mil_derating(result)
        v = IPCValidator(result)
        issues = v.validate()
        # MIL footprint should pass validation
        assert v.is_valid

    def test_pitch_ratio_warning(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(
            family="soic",
            body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)),
            leads=LeadDimensions(width=Tolerance(0.8), length=Tolerance(1.0), pitch=Tolerance(1.0), count=8),
        )
        result = calc.calculate(pkg, density="B")
        v = IPCValidator(result)
        issues = v.validate()
        assert any("IPC-7351-PR-001" in i.rule for i in issues)


class TestSolderPasteExport:
    """Solder paste layer generation."""

    def test_fine_pitch_has_paste_reduction(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(
            family="tssop",
            body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.4), height=Tolerance(1.0)),
            leads=LeadDimensions(width=Tolerance(0.2), length=Tolerance(0.6), pitch=Tolerance(0.5), count=16),
        )
        result = calc.calculate(pkg, density="B")
        output = KiCadModExporter(result).to_string()
        assert "F.Paste" in output

    def test_wide_pitch_no_paste_reduction(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(
            family="soic",
            body=BodyDimensions(length=Tolerance(5.0), width=Tolerance(4.0), height=Tolerance(1.5)),
            leads=LeadDimensions(width=Tolerance(0.4), length=Tolerance(1.0), pitch=Tolerance(1.27), count=8),
        )
        result = calc.calculate(pkg, density="B")
        output = KiCadModExporter(result).to_string()
        # Should not have fp_rect paste layers for wide pitch
        assert "fp_rect" not in output

    def test_tht_no_paste(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(
            family="dip",
            body=BodyDimensions(length=Tolerance(9.3), width=Tolerance(6.4), height=Tolerance(3.5)),
            leads=LeadDimensions(width=Tolerance(0.6), length=Tolerance(2.54), pitch=Tolerance(2.54), count=8),
        )
        result = calc.calculate(pkg, density="B")
        output = KiCadModExporter(result).to_string()
        assert "F.Paste" not in output


class TestFabLayer:
    """Fabrication layer with pin 1 marker."""

    def test_fab_layer_has_pin1_marker(self):
        calc = FootprintCalculator()
        pkg = PackageDefinition(family="chip", body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)))
        result = calc.calculate(pkg, density="B")
        output = KiCadModExporter(result).to_string()
        assert "F.Fab" in output
        assert "fp_circle" in output
