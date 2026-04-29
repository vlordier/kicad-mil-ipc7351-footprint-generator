# SPDX-License-Identifier: GPL-3.0-or-later
"""Batch import — generate footprints from CSV/Excel component lists."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..core.calculator import FootprintCalculator
from ..core.ipc7351 import (
    PackageDefinition,
    BodyDimensions,
    LeadDimensions,
    Tolerance,
    ValidationError,
)
from .kicad_mod import KiCadModExporter
from ..core.naming import NamingConvention


@dataclass
class BatchResult:
    """Summary of a batch import operation."""

    total: int = 0
    succeeded: int = 0
    failed: int = 0
    errors: list[tuple[int, str]] = field(default_factory=list)
    output_dir: Optional[Path] = None


class BatchImporter:
    """Import a CSV/Excel parts list and batch-generate footprints."""

    def __init__(self, output_dir: str | Path, library_name: str = "batch_generated"):
        self.output_dir = Path(output_dir)
        self.library_name = library_name
        self.calculator = FootprintCalculator()
        self._naming = NamingConvention()

    def from_csv(self, csv_path: str | Path) -> BatchResult:
        """Read a CSV file and generate footprints for each row.

        Expected CSV columns: reference,value,family,length,width,height,lead_count,pitch,density,mil
        """
        import csv

        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        result = BatchResult(output_dir=self.output_dir)

        with csv_path.open(newline="") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=1):
                result.total += 1
                try:
                    pkg = self._row_to_package(row)
                    mil = row.get("mil", "").strip().lower() in ("1", "true", "yes", "y")
                    density = row.get("density", "B").strip().upper() or "B"

                    fp_result = self.calculator.calculate(pkg, density=density)
                    if mil:
                        fp_result = self.calculator.apply_mil_derating(fp_result)

                    KiCadModExporter(fp_result, naming=self._naming).write_library(self.output_dir, self.library_name)
                    result.succeeded += 1
                except (ValidationError, ValueError, KeyError) as e:
                    result.failed += 1
                    result.errors.append((row_num, str(e)))

        return result

    def from_excel(self, xlsx_path: str | Path) -> BatchResult:
        """Read an Excel file and generate footprints for each row."""
        import pandas as pd

        xlsx_path = Path(xlsx_path)
        if not xlsx_path.exists():
            raise FileNotFoundError(f"Excel file not found: {xlsx_path}")

        df = pd.read_excel(xlsx_path)
        result = BatchResult(output_dir=self.output_dir)

        for row_num, (_, row) in enumerate(df.iterrows(), start=1):
            result.total += 1
            try:
                r = row.to_dict()
                pkg = self._row_to_package(r)
                mil = str(r.get("mil", "0")).strip().lower() in ("1", "true", "yes", "y")
                density = str(r.get("density", "B")).strip().upper() or "B"

                fp_result = self.calculator.calculate(pkg, density=density)
                if mil:
                    fp_result = self.calculator.apply_mil_derating(fp_result)

                KiCadModExporter(fp_result, naming=self._naming).write_library(self.output_dir, self.library_name)
                result.succeeded += 1
            except (ValidationError, ValueError, KeyError) as e:
                result.failed += 1
                result.errors.append((row_num, str(e)))

        return result

    @staticmethod
    def _row_to_package(row: dict) -> PackageDefinition:
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
            lw = float(row.get("lead_width", 0.3))
            ll = float(row.get("lead_length", 1.0))
            leads = LeadDimensions(
                width=Tolerance(lw, lw * 0.1, lw * 0.1),
                length=Tolerance(ll, ll * 0.1, ll * 0.1),
                pitch=Tolerance(pitch, 0.0, 0.0),
                count=lc,
            )

        return PackageDefinition(family=family, body=body, leads=leads)
