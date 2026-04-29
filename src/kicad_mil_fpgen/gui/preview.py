# SPDX-License-Identifier: GPL-3.0-or-later
"""Live 2D footprint preview using matplotlib."""

from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from ..core.ipc7351 import FootprintResult


class FootprintPreview(QWidget):
    """Widget for rendering a 2D preview of a generated footprint."""

    PAD_COLOR = "lightblue"
    PAD_EDGE = "blue"
    COURTYARD_COLOR = "red"
    SILKSCREEN_COLOR = "yellow"

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.figure = Figure(figsize=(6, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def render(self, result: FootprintResult) -> None:
        """Render the footprint result onto the canvas."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_aspect("equal")
        ax.set_title("Footprint Preview")
        ax.grid(True, alpha=0.3)

        if result.pads:
            for pad in result.pads:
                x = pad.position.x - pad.width / 2
                y = pad.position.y - pad.height / 2
                rect = Rectangle(
                    (x, y),
                    pad.width,
                    pad.height,
                    linewidth=1,
                    edgecolor=self.PAD_EDGE,
                    facecolor=self.PAD_COLOR,
                    alpha=0.7,
                )
                ax.add_patch(rect)

        if result.courtyard:
            cy = result.courtyard
            cy_rect = Rectangle(
                (cy.x_min, cy.y_min),
                cy.x_max - cy.x_min,
                cy.y_max - cy.y_min,
                linewidth=1,
                edgecolor=self.COURTYARD_COLOR,
                facecolor="none",
                linestyle="--",
            )
            ax.add_patch(cy_rect)

        # Auto-scale with margin
        if result.pads:
            all_x = [abs(p.position.x) + p.width / 2 for p in result.pads]
            all_y = [abs(p.position.y) + p.height / 2 for p in result.pads]
            max_extent = max(max(all_x), max(all_y)) + 1.0
        else:
            max_extent = 5.0
        ax.set_xlim(-max_extent, max_extent)
        ax.set_ylim(-max_extent, max_extent)
        self.canvas.draw()
