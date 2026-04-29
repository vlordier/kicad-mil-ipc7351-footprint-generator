# SPDX-License-Identifier: GPL-3.0-or-later
"""Padstack engine — multi-layer pad definitions with custom drill and annular ring rules."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PadShape(Enum):
    RECTANGLE = "rect"
    ROUNDED_RECTANGLE = "rounded_rect"
    OBLONG = "oblong"
    CIRCLE = "circle"
    CUSTOM = "custom"


class PadType(Enum):
    SMD = "smd"
    THT = "tht"
    NSMD = "nsmd"
    VIA = "via"


@dataclass
class LayerPad:
    layer_name: str
    shape: PadShape
    width: float
    height: float
    corner_radius: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 0.0


@dataclass
class DrillDefinition:
    diameter: float = 0.0
    oval: bool = False
    oval_width: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 0.0


@dataclass
class SolderMaskExpansion:
    """Solder mask expansion per IPC-7351."""

    top: float = 0.05
    bottom: float = 0.05

    @classmethod
    def from_density(cls, density: str) -> "SolderMaskExpansion":
        expansions = {
            "A": 0.05,
            "B": 0.075,
            "C": 0.1,
            "MIL": 0.05,
            "USER": 0.075,
        }
        val = expansions.get(density.upper(), 0.075)
        return cls(top=val, bottom=val)


@dataclass
class SolderPasteExpansion:
    """Solder paste expansion per IPC-7525."""

    top: float = 0.0
    bottom: float = 0.0
    reduction_ratio: float = 0.0

    @classmethod
    def from_pitch(cls, pitch_mm: float) -> "SolderPasteExpansion":
        if pitch_mm < 0.5:
            reduction = -0.02
        elif pitch_mm < 0.65:
            reduction = -0.01
        else:
            reduction = 0.0
        return cls(top=reduction, bottom=reduction)


@dataclass
class PadDefinition:
    number: int = 1
    name: str = ""
    pad_type: PadType = PadType.SMD
    layers: list[LayerPad] = field(default_factory=list)
    drill: Optional[DrillDefinition] = None
    solder_mask: SolderMaskExpansion = field(default_factory=SolderMaskExpansion)
    solder_paste: SolderPasteExpansion = field(default_factory=SolderPasteExpansion)
    thermal_relief: bool = False


class PadstackEngine:
    """Engine for creating and validating padstacks."""

    def __init__(self):
        self.pads: list[PadDefinition] = []

    def add_pad(self, pad: PadDefinition) -> None:
        self.pads.append(pad)

    def clear(self) -> None:
        self.pads.clear()

    @staticmethod
    def annular_ring_min(pad_diameter: float, class_: int = 3) -> float:
        """Minimum annular ring per IPC-6012 Class."""
        if class_ >= 3:
            return max(0.05, pad_diameter * 0.02)
        return max(0.025, pad_diameter * 0.015)

    @staticmethod
    def bga_pad(
        ball_diameter: float,
        pitch: float,
        nsmd: bool = True,
    ) -> tuple[float, float]:
        """Calculate BGA pad diameter and solder mask opening.

        Returns (pad_diameter, mask_opening_diameter).
        """
        if nsmd:
            pad_diameter = ball_diameter * 0.85
            mask_opening = pad_diameter + 0.1
        else:
            pad_diameter = ball_diameter * 0.9
            mask_opening = pad_diameter + 0.05

        return (pad_diameter, mask_opening)
