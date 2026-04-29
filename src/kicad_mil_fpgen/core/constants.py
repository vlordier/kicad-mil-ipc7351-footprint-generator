# SPDX-License-Identifier: GPL-3.0-or-later
"""Named constants for the footprint generator — eliminates magic numbers."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PackageFamily(str, Enum):
    """Standard package family identifiers mapped to calculation types."""
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


class CalcType(str, Enum):
    """Internal calculation type that package families map to."""
    CHIP = "chip"
    GULLWING = "gullwing"
    BGA = "bga"
    THT = "tht"


class DensityLevel(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    USER = "USER"
    MANUFACTURER = "MANUFACTURER"


class IPCVersion(str, Enum):
    B = "B"
    C = "C"


# ---------------------------------------------------------------------------
# Mapping — package families → calculation types
# ---------------------------------------------------------------------------

FAMILY_TO_CALC_TYPE: dict[str, CalcType] = {
    PackageFamily.CHIP: CalcType.CHIP,
    PackageFamily.RESISTOR: CalcType.CHIP,
    PackageFamily.CAPACITOR: CalcType.CHIP,
    PackageFamily.INDUCTOR: CalcType.CHIP,
    PackageFamily.SOD: CalcType.GULLWING,
    PackageFamily.SOT: CalcType.GULLWING,
    PackageFamily.SOIC: CalcType.GULLWING,
    PackageFamily.TSSOP: CalcType.GULLWING,
    PackageFamily.QFP: CalcType.GULLWING,
    PackageFamily.QFN: CalcType.GULLWING,
    PackageFamily.DFN: CalcType.GULLWING,
    PackageFamily.BGA: CalcType.BGA,
    PackageFamily.LGA: CalcType.BGA,
    PackageFamily.CSP: CalcType.BGA,
    PackageFamily.DIP: CalcType.THT,
    PackageFamily.SIP: CalcType.THT,
    PackageFamily.THT: CalcType.THT,
    PackageFamily.AXIAL: CalcType.THT,
    PackageFamily.RADIAL: CalcType.THT,
}


# ---------------------------------------------------------------------------
# Per-family density factors (typed dataclass)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChipFactors:
    heel: float
    toe: float
    side: float
    courtyard: float


@dataclass(frozen=True)
class GullwingFactors:
    heel: float
    toe: float
    side: float
    courtyard: float


@dataclass(frozen=True)
class BgaFactors:
    nsmd_ratio: float
    smd_ratio: float
    courtyard: float


@dataclass(frozen=True)
class ThtFactors:
    annular_extra: float
    courtyard: float


# Type union for all factor types
FamilyFactors = ChipFactors | GullwingFactors | BgaFactors | ThtFactors


# Density A (Most) = largest pads for maximum solder joint strength
# Density C (Least) = smallest pads for high-density designs
FAMILY_FACTORS: dict[CalcType, dict[DensityLevel, FamilyFactors]] = {
    CalcType.CHIP: {
        DensityLevel.A: ChipFactors(heel=0.25, toe=0.60, side=0.25, courtyard=0.50),
        DensityLevel.B: ChipFactors(heel=0.20, toe=0.50, side=0.20, courtyard=0.25),
        DensityLevel.C: ChipFactors(heel=0.15, toe=0.40, side=0.15, courtyard=0.10),
    },
    CalcType.GULLWING: {
        DensityLevel.A: GullwingFactors(heel=0.30, toe=0.65, side=0.20, courtyard=0.50),
        DensityLevel.B: GullwingFactors(heel=0.25, toe=0.55, side=0.15, courtyard=0.25),
        DensityLevel.C: GullwingFactors(heel=0.20, toe=0.45, side=0.10, courtyard=0.10),
    },
    CalcType.BGA: {
        DensityLevel.A: BgaFactors(nsmd_ratio=0.90, smd_ratio=0.95, courtyard=0.50),
        DensityLevel.B: BgaFactors(nsmd_ratio=0.85, smd_ratio=0.90, courtyard=0.25),
        DensityLevel.C: BgaFactors(nsmd_ratio=0.80, smd_ratio=0.85, courtyard=0.10),
    },
    CalcType.THT: {
        DensityLevel.A: ThtFactors(annular_extra=0.15, courtyard=0.50),
        DensityLevel.B: ThtFactors(annular_extra=0.10, courtyard=0.25),
        DensityLevel.C: ThtFactors(annular_extra=0.05, courtyard=0.10),
    },
}

# Default fallback when density not found
FAMILY_FACTORS_DEFAULT_DENSITY: dict[CalcType, DensityLevel] = {
    ct: DensityLevel.B for ct in CalcType
}


# ---------------------------------------------------------------------------
# MIL derating constants
# ---------------------------------------------------------------------------

MIL_DERATING_PAD_INCREMENT: float = 0.05
"""Amount added to each pad dimension (mm) when MIL derating is applied."""

MIL_DERATING_COURTYARD_INCREMENT: float = 0.1
"""Amount added to each courtyard edge (mm) when MIL derating is applied."""


# ---------------------------------------------------------------------------
# Density multiplier
# ---------------------------------------------------------------------------

DENSITY_MULTIPLIERS: dict[DensityLevel, float] = {
    DensityLevel.A: 1.0,
    DensityLevel.B: 0.8,
    DensityLevel.C: 0.5,
    DensityLevel.USER: 0.75,
    DensityLevel.MANUFACTURER: 0.65,
}


# ---------------------------------------------------------------------------
# KiCad export constants
# ---------------------------------------------------------------------------

KICAD_LAYERS_SMD: str = '"F.Cu" "F.Paste" "F.Mask"'
KICAD_LAYERS_THT: str = '"F.Cu" "B.Cu"'

KICAD_FP_VERSION: str = "20240101"
KICAD_GENERATOR_NAME: str = "kicad-mil-ipc7351"

COURTYARD_LINE_WIDTH: float = 0.05
SILKSCREEN_LINE_WIDTH: float = 0.12
SILKSCREEN_OFFSET: float = 0.1
"""Offset of silkscreen outline beyond body edge (mm)."""

ANNULAR_RING_BASE: float = 0.15
"""Base annular ring added on top of density-specific annular_extra (mm)."""

PASTE_REDUCTION_RATIO: float = 0.1
"""Solder paste area reduction ratio for fine-pitch components (< 0.65mm pitch)."""

PASTE_REDUCTION_RATIO: float = 0.1
"""Solder paste area reduction ratio for fine-pitch components (< 0.65mm pitch)."""
