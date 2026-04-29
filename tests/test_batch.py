# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the batch import module."""

import tempfile
from pathlib import Path

import pytest

from kicad_mil_fpgen.export.batch_import import BatchImporter, BatchResult


def test_csv_import_creates_files():
    csv_content = (
        "reference,value,family,length,width,height,lead_count,pitch,density,mil\n"
        "C1,10uF,chip,3.2,1.6,0.55,0,0,B,no\n"
        "C2,100nF,chip,1.6,0.8,0.45,0,0,A,yes\n"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "parts.csv"
        csv_path.write_text(csv_content)
        importer = BatchImporter(tmpdir)
        result = importer.from_csv(csv_path)
        assert result.total == 2
        assert result.succeeded == 2
        assert result.failed == 0


def test_csv_import_defaults():
    csv_content = "reference,value,family,length,width\nR1,10k,chip,3.2,1.6\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "parts.csv"
        csv_path.write_text(csv_content)
        importer = BatchImporter(tmpdir)
        result = importer.from_csv(csv_path)
        assert result.succeeded == 1


def test_csv_import_file_not_found():
    importer = BatchImporter("/tmp/nonexistent")
    with pytest.raises(FileNotFoundError):
        importer.from_csv("/tmp/nonexistent/missing.csv")


def test_csv_import_empty_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "empty.csv"
        csv_path.write_text("reference,value,family,length,width\n")
        importer = BatchImporter(tmpdir)
        result = importer.from_csv(csv_path)
        assert result.total == 0
        assert result.succeeded == 0


def test_csv_import_invalid_data():
    csv_content = (
        "reference,value,family,length,width\n"
        "R1,10k,chip,not_a_number,1.6\n"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "bad.csv"
        csv_path.write_text(csv_content)
        importer = BatchImporter(tmpdir)
        result = importer.from_csv(csv_path)
        assert result.total == 1
        assert result.failed == 1
        assert len(result.errors) == 1


def test_csv_import_zero_dimensions():
    csv_content = (
        "reference,value,family,length,width\n"
        "R1,10k,chip,0,1.6\n"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "zero.csv"
        csv_path.write_text(csv_content)
        importer = BatchImporter(tmpdir)
        result = importer.from_csv(csv_path)
        assert result.failed == 1


def test_csv_import_mil_flag():
    csv_content = (
        "reference,value,family,length,width,mil\n"
        "R1,10k,chip,3.2,1.6,yes\n"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "mil.csv"
        csv_path.write_text(csv_content)
        importer = BatchImporter(tmpdir)
        result = importer.from_csv(csv_path)
        assert result.succeeded == 1


def test_csv_import_gullwing():
    csv_content = (
        "reference,value,family,length,width,lead_count,pitch\n"
        "U1,OpAmp,soic,5.0,4.0,8,1.27\n"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "gull.csv"
        csv_path.write_text(csv_content)
        importer = BatchImporter(tmpdir)
        result = importer.from_csv(csv_path)
        assert result.succeeded == 1
        lib = Path(tmpdir) / "batch_generated.pretty"
        assert lib.exists()
        fps = list(lib.glob("*.kicad_mod"))
        assert len(fps) > 0


def test_batch_result_counts():
    r = BatchResult(total=10, succeeded=7, failed=3)
    assert r.total == 10
    assert r.succeeded == 7
    assert r.failed == 3


def test_batch_result_errors():
    r = BatchResult()
    r.errors.append((1, "Invalid body length"))
    r.errors.append((3, "Missing ball diameter"))
    assert len(r.errors) == 2
    assert r.errors[0][0] == 1


def test_csv_import_multiple_libraries():
    csv_content = (
        "reference,value,family,length,width\n"
        "R1,10k,chip,3.2,1.6\n"
        "R2,100k,chip,1.6,0.8\n"
        "C1,10uF,chip,2.0,1.25\n"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "multi.csv"
        csv_path.write_text(csv_content)
        importer = BatchImporter(tmpdir, library_name="my_lib")
        result = importer.from_csv(csv_path)
        assert result.succeeded == 3
        lib = Path(tmpdir) / "my_lib.pretty"
        assert lib.exists()
        fps = list(lib.glob("*.kicad_mod"))
        assert len(fps) == 3
