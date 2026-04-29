"""Package data model — user-facing representation of a component package."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class PackageFamily(Enum):
    CHIP = "chip"
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
    AXIAL = "axial"
    RADIAL = "radial"
    CONNECTOR = "connector"
    CUSTOM = "custom"


@dataclass
class PackageModel:
    name: str = ""
    description: str = ""
    family: PackageFamily = PackageFamily.CHIP
    manufacturer: str = ""
    datasheet: str = ""

    body_length: float = 0.0
    body_width: float = 0.0
    body_height: float = 0.0
    body_length_tol: float = 0.0
    body_width_tol: float = 0.0
    body_height_tol: float = 0.0

    lead_count: int = 0
    lead_pitch: float = 0.0
    lead_width: float = 0.0
    lead_length: float = 0.0
    lead_width_tol: float = 0.0
    lead_length_tol: float = 0.0
    lead_span: float = 0.0

    ball_diameter: float = 0.0
    ball_count: int = 0

    pad_width: float = 0.0
    pad_height: float = 0.0
    pad_shape: str = "rounded_rect"

    density: str = "B"
    mil_grade: bool = False
    mil_derating: bool = False
    mil_notes: str = ""
