# SPDX-License-Identifier: GPL-3.0-or-later
"""Abstract base class for package family calculators.

Each package family (chip, gullwing, BGA, THT) implements this interface
and registers itself via the FamilyRegistry. New families can be added
without modifying any core code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Optional

from ..constants import (
    CalcType,
    DensityLevel,
    FamilyFactors,
    ChipFactors,
    GullwingFactors,
    BgaFactors,
    ThtFactors,
    FAMILY_FACTORS,
    FAMILY_FACTORS_DEFAULT_DENSITY,
    ANNULAR_RING_BASE,
)
from ..tolerances import Tolerance
from ..ipc7351 import (
    PackageDefinition,
    BodyDimensions,
    LeadDimensions,
    PadDimensions,
    PadPosition,
    PadShape,
    Courtyard,
    FootprintResult,
    FootprintError,
    ValidationError,
)


@dataclass
class FamilyMetadata:
    """Metadata about a registered family."""
    name: str
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    requires_leads: bool = False
    requires_ball: bool = False
    calc_type: CalcType = CalcType.CHIP


class FootprintFamily(ABC):
    """Abstract interface for a package family calculator."""

    metadata: ClassVar[FamilyMetadata]

    @classmethod
    @abstractmethod
    def get_factors(cls, density: str) -> FamilyFactors:
        ...

    @classmethod
    def validate(cls, pkg: PackageDefinition) -> None:
        family_meta = cls.metadata
        if family_meta.requires_leads and pkg.leads is None:
            raise ValidationError(f"{family_meta.name} requires lead dimensions")
        if family_meta.requires_ball and pkg.ball_diameter is None:
            raise ValidationError(f"{family_meta.name} requires ball diameter")
        if pkg.body is None:
            raise ValidationError("Body dimensions are required")

    @classmethod
    @abstractmethod
    def calculate(cls, pkg: PackageDefinition, factors: FamilyFactors, result: FootprintResult) -> None:
        ...

    @classmethod
    def get_yaml_config_template(cls) -> dict:
        """Return a YAML-serializable config dict for this family."""
        return {
            "aliases": cls.metadata.aliases,
            "description": cls.metadata.description,
        }
