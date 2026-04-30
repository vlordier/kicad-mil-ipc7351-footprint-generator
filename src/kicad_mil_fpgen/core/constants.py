# SPDX-License-Identifier: GPL-3.0-or-later
"""Named constants — eliminates magic numbers."""

from enum import Enum


class DensityLevel(str, Enum):
    A = "A"
    B = "B"
    C = "C"


# Per-family density factors (mm). Density A = largest pads (MIL preferred).
FAMILY_FACTORS: dict[str, dict[str, dict]] = {
    "chip": {
        "A": {"heel": 0.25, "toe": 0.60, "side": 0.25, "courtyard": 0.50},
        "B": {"heel": 0.20, "toe": 0.50, "side": 0.20, "courtyard": 0.25},
        "C": {"heel": 0.15, "toe": 0.40, "side": 0.15, "courtyard": 0.10},
    },
    "gullwing": {
        "A": {"heel": 0.30, "toe": 0.65, "side": 0.20, "courtyard": 0.50},
        "B": {"heel": 0.25, "toe": 0.55, "side": 0.15, "courtyard": 0.25},
        "C": {"heel": 0.20, "toe": 0.45, "side": 0.10, "courtyard": 0.10},
    },
    "bga": {
        "A": {"nsmd_ratio": 0.90, "courtyard": 0.50},
        "B": {"nsmd_ratio": 0.85, "courtyard": 0.25},
        "C": {"nsmd_ratio": 0.80, "courtyard": 0.10},
    },
    "tht": {
        "A": {"annular_extra": 0.15, "courtyard": 0.50},
        "B": {"annular_extra": 0.10, "courtyard": 0.25},
        "C": {"annular_extra": 0.05, "courtyard": 0.10},
    },
}

FAMILY_KEY_MAP: dict[str, str] = {
    "chip": "chip", "resistor": "chip", "capacitor": "chip", "inductor": "chip",
    "sot": "gullwing", "sod": "gullwing", "soic": "gullwing", "tssop": "gullwing",
    "qfp": "gullwing", "qfn": "gullwing", "dfn": "gullwing",
    "bga": "bga",
    "dip": "tht", "sip": "tht", "tht": "tht", "axial": "tht", "radial": "tht",
}

# MIL derating
MIL_PAD_INCREMENT: float = 0.05
MIL_COURTYARD_INCREMENT: float = 0.1

# Annular ring
ANNULAR_RING_BASE: float = 0.15

# Default tolerances (percentage of nominal)
BODY_LENGTH_TOLERANCE_PCT: float = 0.05
BODY_WIDTH_TOLERANCE_PCT: float = 0.05
BODY_HEIGHT_TOLERANCE_PCT: float = 0.10
LEAD_WIDTH_TOLERANCE_PCT: float = 0.10
LEAD_LENGTH_TOLERANCE_PCT: float = 0.10

# Default dimensions (mm)
DEFAULT_BODY_HEIGHT_MM: float = 0.5
DEFAULT_LEAD_WIDTH_MM: float = 0.3
DEFAULT_LEAD_LENGTH_MM: float = 1.0
DEFAULT_LEAD_PITCH_MM: float = 1.27
DEFAULT_BODY_HEIGHT_CSV_MM: float = 0.5

# Courtyard / silkscreen / fab (mm)
COURTYARD_LINE_WIDTH_MM: float = 0.05
SILKSCREEN_CLEARANCE_MM: float = 0.1
SILKSCREEN_LINE_WIDTH_MM: float = 0.12
FAB_MARKER_RADIUS_MM: float = 0.5
FAB_LINE_WIDTH_MM: float = 0.1

# Thermal pad
THERMAL_PAD_RATIO: float = 0.7
THERMAL_PAD_CORNER_RADIUS_MM: float = 0.2

# BGA defaults
BGA_DEFAULT_PITCH_MM: float = 0.75
BGA_PITCH_SCALE: float = 0.85

# Auto-tolerance ratio when no tolerance given
AUTO_TOLERANCE_RATIO: float = 0.1
