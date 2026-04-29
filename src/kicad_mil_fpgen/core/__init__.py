# SPDX-License-Identifier: GPL-3.0-or-later

from .ipc7351 import PackageDefinition, BodyDimensions, LeadDimensions, Tolerance, FootprintResult, PadDimensions, PadPosition, Courtyard, FootprintError, ValidationError
from .padstack import PadstackEngine, PadShape, PadType
from .tolerances import ToleranceEngine, ToleranceStack, ToleranceMethod, ToleranceStackResult
from .calculator import FootprintCalculator
from .constants import (
    PackageFamily, CalcType, DensityLevel, FamilyFactors,
    ChipFactors, GullwingFactors, BgaFactors, ThtFactors,
    FAMILY_TO_CALC_TYPE, FAMILY_FACTORS, FAMILY_FACTORS_DEFAULT_DENSITY,
    DENSITY_MULTIPLIERS, MIL_DERATING_PAD_INCREMENT, MIL_DERATING_COURTYARD_INCREMENT,
    KICAD_LAYERS_SMD, KICAD_LAYERS_THT, ANNULAR_RING_BASE,
)
from .registry import resolve_family, get_registered_families, get_known_names

__all__ = [
    "PackageDefinition", "BodyDimensions", "LeadDimensions",
    "Tolerance", "FootprintResult", "PadDimensions", "PadPosition", "Courtyard",
    "FootprintError", "ValidationError",
    "PadstackEngine", "PadShape", "PadType",
    "ToleranceEngine", "ToleranceStack", "ToleranceMethod", "ToleranceStackResult",
    "FootprintCalculator",
    "PackageFamily", "CalcType", "DensityLevel", "FamilyFactors",
    "ChipFactors", "GullwingFactors", "BgaFactors", "ThtFactors",
    "FAMILY_TO_CALC_TYPE", "FAMILY_FACTORS", "FAMILY_FACTORS_DEFAULT_DENSITY",
    "DENSITY_MULTIPLIERS", "MIL_DERATING_PAD_INCREMENT", "MIL_DERATING_COURTYARD_INCREMENT",
    "KICAD_LAYERS_SMD", "KICAD_LAYERS_THT", "ANNULAR_RING_BASE",
    "resolve_family", "get_registered_families", "get_known_names",
]
