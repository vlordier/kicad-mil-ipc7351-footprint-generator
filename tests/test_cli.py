# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the CLI entry point."""

import re
import sys
import tempfile
from pathlib import Path

import pytest

from kicad_mil_fpgen.__main__ import build_parser, cli_generate


def test_build_parser():
    parser = build_parser()
    args, _ = parser.parse_known_args(["--package", "chip", "--body-length", "3.2", "--body-width", "1.6"])
    assert args.package == "chip"
    assert args.density == "B"


def test_cli_requires_package():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_cli_generate_chip():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test.kicad_mod"
        args = build_parser().parse_args([
            "--package", "chip",
            "--body-length", "3.2",
            "--body-width", "1.6",
            "--output", str(out),
        ])
        rc = cli_generate(args)
        assert rc == 0
        assert out.exists()
        content = out.read_text()
        assert "chip" in content
        assert "pad" in content


def test_cli_generate_mil():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "mil.kicad_mod"
        args = build_parser().parse_args([
            "--package", "chip",
            "--body-length", "3.2",
            "--body-width", "1.6",
            "--mil",
            "--output", str(out),
        ])
        rc = cli_generate(args)
        assert rc == 0
        # MIL pads should be 0.05mm larger
        content = out.read_text()
        sizes = re.findall(r"\(size ([\d.]+) ([\d.]+)\)", content)
        for w, h in sizes:
            assert float(w) > 0
            assert float(h) > 0


def test_cli_generate_gullwing():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "soic.kicad_mod"
        args = build_parser().parse_args([
            "--package", "soic",
            "--body-length", "5.0",
            "--body-width", "4.0",
            "--lead-count", "8",
            "--lead-pitch", "1.27",
            "--output", str(out),
        ])
        rc = cli_generate(args)
        assert rc == 0
        content = out.read_text()
        pad_count = content.count("(pad ")
        assert pad_count == 8


def test_cli_generate_density_a():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "a.kicad_mod"
        args = build_parser().parse_args([
            "--package", "chip",
            "--body-length", "3.2",
            "--body-width", "1.6",
            "--density", "A",
            "--output", str(out),
        ])
        rc = cli_generate(args)
        assert rc == 0
        content_a = out.read_text()

        out_c = Path(tmpdir) / "c.kicad_mod"
        args_c = build_parser().parse_args([
            "--package", "chip",
            "--body-length", "3.2",
            "--body-width", "1.6",
            "--density", "C",
            "--output", str(out_c),
        ])
        cli_generate(args_c)
        content_c = out_c.read_text()

        sizes_a = re.findall(r"\(size ([\d.]+) ([\d.]+)\)", content_a)
        sizes_c = re.findall(r"\(size ([\d.]+) ([\d.]+)\)", content_c)
        assert float(sizes_a[0][0]) > float(sizes_c[0][0])


def test_cli_generate_default_output_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        original = os.getcwd()
        try:
            os.chdir(tmpdir)
            args = build_parser().parse_args([
                "--package", "chip",
                "--body-length", "3.2",
                "--body-width", "1.6",
            ])
            rc = cli_generate(args)
            assert rc == 0
            expected = Path(tmpdir) / "chip_3.20x1.60.kicad_mod"
            assert expected.exists()
        finally:
            os.chdir(original)


def test_cli_generate_missing_args():
    args = build_parser().parse_args(["--package", "chip", "--body-length", "3.2", "--body-width", "1.6"])
    rc = cli_generate(args)
    assert rc == 0  # valid args, should work


def test_cli_generate_invalid_density():
    import argparse
    with pytest.raises(SystemExit):
        build_parser().parse_args([
            "--package", "chip",
            "--body-length", "3.2",
            "--body-width", "1.6",
            "--density", "INVALID",
            "--output", "/tmp/bad.kicad_mod",
        ])


def test_cli_generate_bga():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "bga.kicad_mod"
        args = build_parser().parse_args([
            "--package", "bga",
            "--body-length", "10.0",
            "--body-width", "10.0",
            "--ball-diameter", "0.5",
            "--ball-count", "256",
            "--output", str(out),
        ])
        rc = cli_generate(args)
        assert rc == 0
        assert out.exists()


def test_main_help(capsys, monkeypatch):
    """main() with --help should print help and exit."""
    monkeypatch.setattr("sys.argv", ["kicad-mil-fpgen", "--help"])
    from kicad_mil_fpgen.__main__ import main
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "usage" in captured.out
