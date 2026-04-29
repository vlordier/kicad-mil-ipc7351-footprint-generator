# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the batch import module."""

import tempfile
from pathlib import Path

from kicad_mil_fpgen.export.batch_import import BatchImporter


def test_csv_import_creates_files():
    csv_content = "reference,value,family,length,width,height,lead_count,pitch,density,mil\nC1,10uF,chip,3.2,1.6,0.55,0,0,B,no\nC2,100nF,chip,1.6,0.8,0.45,0,0,A,yes\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "parts.csv"
        csv_path.write_text(csv_content)

        importer = BatchImporter(tmpdir)
        result_paths = importer.from_csv(csv_path)
        assert len(result_paths) == 2


def test_csv_import_defaults():
    csv_content = "reference,value,family,length,width\nR1,10k,chip,3.2,1.6\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "parts.csv"
        csv_path.write_text(csv_content)

        importer = BatchImporter(tmpdir)
        result_paths = importer.from_csv(csv_path)
        assert len(result_paths) == 1
