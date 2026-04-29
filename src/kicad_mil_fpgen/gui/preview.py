"""Live 2D footprint preview using matplotlib."""

from typing import Optional

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from ..core.ipc7351 import FootprintResult


class FootprintPreview(QWidget):
    """Widget for rendering a 2D preview of a generated footprint."""

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
            for i, pad in enumerate(result.pads):
                rect = plt.Rectangle(
                    (-pad.width / 2, i * 1.5 - pad.height / 2),
                    pad.width,
                    pad.height,
                    linewidth=1,
                    edgecolor="blue",
                    facecolor="lightblue",
                    alpha=0.7,
                )
                ax.add_patch(rect)

        if result.courtyard:
            cy = result.courtyard
            cy_rect = plt.Rectangle(
                (cy.x_min, cy.y_min),
                cy.x_max - cy.x_min,
                cy.y_max - cy.y_min,
                linewidth=1,
                edgecolor="red",
                facecolor="none",
                linestyle="--",
            )
            ax.add_patch(cy_rect)

        margin = 1.0
        ax.set_xlim(-5, 5)
        ax.set_ylim(-5, 5)
        self.canvas.draw()


import matplotlib.pyplot as plt
