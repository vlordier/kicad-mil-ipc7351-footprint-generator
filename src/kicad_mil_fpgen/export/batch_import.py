# SPDX-License-Identifier: GPL-3.0-or-later
"""Batch import — generate footprints from CSV/Excel component lists."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

from ..core.ipc7351 import (
    IPC7351Calculator,
    PackageDefinition,
    BodyDimensions,
    LeadDimensions,
    Tolerance,
)
from .kicad_mod import KiCadModExporter


@dataclass
class BatchRow:
    reference: str = ""
    value: str = ""
    package_family: str = "chip"
    body_length: float = 0.0
    body_width: float = 0.0
    body_height: float = 0.0
    lead_count: int = 0
    lead_pitch: float = 0.0
    density: str = "B"
    mil_grade: bool = False


class BatchImporter:
    """Import a CSV/Excel parts list and batch-generate footprints."""

    def __init__(self, output_dir: str | Path, library_name: str = "batch_generated"):
        self.output_dir = Path(output_dir)
        self.library_name = library_name
        self.calculator = IPC7351Calculator(ipc_version="C")

    def from_csv(self, csv_path: str | Path) -> list[Path]:
        """Read a CSV file and generate footprints for each row.

        Expected CSV columns: reference,value,family,length,width,height,lead_count,pitch,density,mil
        """
        import csv

        csv_path = Path(csv_path)
        generated: list[Path] = []

        with csv_path.open(newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pkg = self._row_to_package(row)
                mil = row.get("mil", "").strip().lower() in ("1", "true", "yes", "y")
                density = row.get("density", "B").strip().upper() or "B"

                result = self.calculator.calculate_footprint(pkg, density=density)
                if mil:
                    result = self.calculator.apply_mil_derating(result)

                exporter = KiCadModExporter(result)
                lib_path = exporter.write_library(self.output_dir, self.library_name)
                generated.append(lib_path)

        return generated

    def from_excel(self, xlsx_path: str | Path) -> list[Path]:
        """Read an Excel file and generate footprints for each row."""
        import pandas as pd

        xlsx_path = Path(xlsx_path)
        df = pd.read_excel(xlsx_path)
        generated: list[Path] = []

        for _, row in df.iterrows():
            r = row.to_dict()
            pkg = self._row_to_package(r)
            mil = str(r.get("mil", "0")).strip().lower() in ("1", "true", "yes", "y")
            density = str(r.get("density", "B")).strip().upper() or "B"

            result = self.calculator.calculate_footprint(pkg, density=density)
            if mil:
                result = self.calculator.apply_mil_derating(result)

            exporter = KiCadModExporter(result)
            lib_path = exporter.write_library(self.output_dir, self.library_name)
            generated.append(lib_path)

        return generated

    def _row_to_package(self, row: dict) -> PackageDefinition:
        family = str(row.get("family", row.get("package_family", "chip"))).strip().lower()
        bl = float(row.get("length", row.get("body_length", 0)))
        bw = float(row.get("width", row.get("body_width", 0)))
        bh = float(row.get("height", row.get("body_height", 0.5)))

        body = BodyDimensions(
            length=Tolerance(bl, bl * 0.05, bl * 0.05),
            width=Tolerance(bw, bw * 0.05, bw * 0.05),
            height=Tolerance(bh, bh * 0.1, bh * 0.1),
        )

        leads = None
        lc_str = str(row.get("lead_count", row.get("leads", "0")))
        lc = int(lc_str) if lc_str.lstrip("-").isdigit() else 0
        pitch = float(row.get("pitch", row.get("lead_pitch", 0)))
        if lc > 0 and pitch > 0:
            leads = LeadDimensions(
                width=Tolerance(0.3, 0.05, 0.05),
                length=Tolerance(1.0, 0.1, 0.1),
                pitch=Tolerance(pitch, 0.0, 0.0),
                count=lc,
            )

        return PackageDefinition(family=family, body=body, leads=leads)
