# SPDX-License-Identifier: GPL-3.0-or-later
"""Batch import — generate footprints from CSV component lists."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..core.families import calculate, apply_mil_derating
from ..core.ipc7351 import (
    PackageDefinition, BodyDimensions, LeadDimensions, Tolerance, ValidationError,
)
from .kicad_mod import KiCadModExporter


@dataclass
class BatchResult:
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    errors: list[tuple[int, str]] = field(default_factory=list)


class BatchImporter:
    def __init__(self, output_dir: str | Path, library_name: str = "batch_generated"):
        self.output_dir = Path(output_dir)
        self.library_name = library_name

    def from_csv(self, csv_path: str | Path) -> BatchResult:
        import csv
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")

        result = BatchResult()
        with csv_path.open(newline="") as f:
            for row_num, row in enumerate(csv.DictReader(f), 1):
                result.total += 1
                try:
                    pkg = self._row_to_package(row)
                    mil = row.get("mil", "").strip().lower() in ("1", "true", "yes", "y")
                    density = row.get("density", "B").strip().upper() or "B"
                    fp_result = calculate(pkg, density=density)
                    if mil:
                        fp_result = apply_mil_derating(fp_result)
                    KiCadModExporter(fp_result).write_library(self.output_dir, self.library_name)
                    result.succeeded += 1
                except (ValidationError, ValueError, KeyError) as e:
                    result.failed += 1
                    result.errors.append((row_num, str(e)))
        return result

    @staticmethod
    def _row_to_package(row: dict) -> PackageDefinition:
        family = str(row.get("family", "chip")).strip().lower()
        bl = float(row.get("length", row.get("body_length", 0)))
        bw = float(row.get("width", row.get("body_width", 0)))
        bh = float(row.get("height", row.get("body_height", 0.5)))
        body = BodyDimensions(length=Tolerance(bl, bl * 0.05, bl * 0.05),
                              width=Tolerance(bw, bw * 0.05, bw * 0.05),
                              height=Tolerance(bh, bh * 0.1, bh * 0.1))
        leads = None
        lc = int(row.get("lead_count", 0))
        pitch = float(row.get("pitch", row.get("lead_pitch", 0)))
        if lc > 0 and pitch > 0:
            lw = float(row.get("lead_width", 0.3))
            ll = float(row.get("lead_length", 1.0))
            leads = LeadDimensions(width=Tolerance(lw, lw * 0.1, lw * 0.1),
                                   length=Tolerance(ll, ll * 0.1, ll * 0.1),
                                   pitch=Tolerance(pitch, 0.0, 0.0), count=lc)
        return PackageDefinition(family=family, body=body, leads=leads)
