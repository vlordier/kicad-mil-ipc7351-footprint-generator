# SPDX-License-Identifier: GPL-3.0-or-later
"""Named constants — eliminates magic numbers."""

from enum import Enum
from dataclasses import dataclass


class PackageFamily(str, Enum):
    CHIP = "chip"
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    SOD = "sod"
    SOT = "sot"
    SOIC = "soic"
    TSSOP = "tssop"
    QFP = "qfp"
    QFN = "qfn"
    DFN = "dfn"
    BGA = "bga"
    LGA = "lga"
    CSP = "csp"
    DIP = "dip"
    SIP = "sip"
    THT = "tht"
    AXIAL = "axial"
    RADIAL = "radial"


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
    "bga": "bga", "lga": "bga", "csp": "bga",
    "dip": "tht", "sip": "tht", "tht": "tht", "axial": "tht", "radial": "tht",
}

# MIL derating
MIL_PAD_INCREMENT: float = 0.05
MIL_COURTYARD_INCREMENT: float = 0.1

# Solder mask / paste defaults
MASK_EXPANSION: dict[str, float] = {"A": 0.05, "B": 0.075, "C": 0.1}
ANNULAR_RING_BASE: float = 0.15
