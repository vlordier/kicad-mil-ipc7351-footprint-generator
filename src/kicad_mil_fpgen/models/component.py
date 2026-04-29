# SPDX-License-Identifier: GPL-3.0-or-later
"""Component data model — a component with reference designator, value, and package."""

from dataclasses import dataclass, field
from typing import Optional

from .package import PackageModel


@dataclass
class ComponentModel:
    reference: str = ""
    value: str = ""
    package: Optional[PackageModel] = None
    manufacturer: str = ""
    part_number: str = ""
    datasheet: str = ""
    mil_spec: str = ""

    def __post_init__(self):
        if self.package is None:
            self.package = PackageModel()
