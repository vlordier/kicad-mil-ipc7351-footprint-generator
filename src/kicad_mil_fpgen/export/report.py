# SPDX-License-Identifier: GPL-3.0-or-later
"""PDF report generator — produces a calculation report for design documentation."""

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors

from ..core.ipc7351 import FootprintResult


class PDFReportGenerator:
    """Generate a PDF report documenting all calculations for a footprint."""

    def __init__(self, result: FootprintResult):
        self.result = result

    def generate(self, output_path: str | Path) -> None:
        """Write the PDF report."""
        output_path = Path(output_path)
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            title="Footprint Calculation Report",
            author="KiCad MIL IPC-7351 Footprint Generator",
        )
        styles = getSampleStyleSheet()
        elements: list = []

        elements.append(Paragraph("Footprint Calculation Report", styles["Title"]))
        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph(f"IPC Version: IPC-7351{self.result.ipc_version}", styles["Normal"]))
        elements.append(Paragraph(f"Density Level: {self.result.density}", styles["Normal"]))

        if self.result.package:
            pkg = self.result.package
            elements.append(Spacer(1, 3 * mm))
            elements.append(Paragraph(f"Package: {pkg.family}", styles["Heading2"]))

            if pkg.body:
                elements.append(Paragraph(f"Body: {pkg.body.length.nominal:.3f} × {pkg.body.width.nominal:.3f} × {pkg.body.height.nominal:.3f} mm", styles["Normal"]))

        if self.result.formulas_used:
            elements.append(Spacer(1, 3 * mm))
            elements.append(Paragraph("Formulas Used", styles["Heading2"]))
            data = [["Parameter", "Formula", "Result"]]
            for name, detail in self.result.formulas_used.items():
                data.append([name, detail, ""])
            t = Table(data, colWidths=[60*mm, 100*mm, 30*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.8, 0.8, 0.8)),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]))
            elements.append(t)

        if self.result.notes:
            elements.append(Spacer(1, 3 * mm))
            elements.append(Paragraph("Notes", styles["Heading2"]))
            for note in self.result.notes:
                elements.append(Paragraph(f"• {note}", styles["Normal"]))

        if self.result.warnings:
            elements.append(Spacer(1, 3 * mm))
            elements.append(Paragraph("Warnings", styles["Heading2"]))
            for w in self.result.warnings:
                elements.append(Paragraph(f"⚠ {w}", styles["Normal"]))

        doc.build(elements)
