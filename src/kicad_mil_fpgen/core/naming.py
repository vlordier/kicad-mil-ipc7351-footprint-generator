# SPDX-License-Identifier: GPL-3.0-or-later
"""Footprint naming conventions — IPC-7351, MIL, and custom styles.

Generates deterministic, human-readable footprint names from package
dimensions, density level, and profile settings.
"""

from __future__ import annotations

from typing import Optional

from .ipc7351 import FootprintResult, PackageDefinition
from .constants import DensityLevel


class NamingConvention:
    """Generates footprint names based on style and profile settings."""

    def __init__(
        self,
        style: str = "ipc7351",
        prefix: str = "",
        suffix: str = "",
        include_density: bool = True,
        include_version: bool = False,
        separator: str = "_",
    ) -> None:
        self.style = style
        self.prefix = prefix
        self.suffix = suffix
        self.include_density = include_density
        self.include_version = include_version
        self.separator = separator

    def generate(self, result: FootprintResult) -> str:
        pkg = result.package
        if pkg is None or pkg.body is None:
            return "unnamed_footprint"

        if self.style == "mil":
            name = self._mil_name(pkg, result)
        elif self.style == "custom":
            name = self._custom_name(pkg, result)
        else:
            name = self._ipc7351_name(pkg, result)

        parts = []
        if self.prefix:
            parts.append(self.prefix)
        parts.append(name)
        if self.suffix:
            parts.append(self.suffix)
        return self.separator.join(parts)

    def _ipc7351_name(self, pkg: PackageDefinition, result: FootprintResult) -> str:
        bl = pkg.body.length.nominal
        bw = pkg.body.width.nominal
        parts = [pkg.family, f"{bl:.2f}x{bw:.2f}"]

        if self.include_density:
            parts.append(result.density)
        if self.include_version:
            parts.append(f"IPC{result.ipc_version}")

        return self.separator.join(parts)

    def _mil_name(self, pkg: PackageDefinition, result: FootprintResult) -> str:
        bl = pkg.body.length.nominal
        bw = pkg.body.width.nominal
        parts = [
            "MIL",
            pkg.family.upper(),
            f"{bl:.2f}x{bw:.2f}",
            result.density,
            f"IPC{result.ipc_version}",
        ]
        return self.separator.join(parts)

    def _custom_name(self, pkg: PackageDefinition, result: FootprintResult) -> str:
        bl = pkg.body.length.nominal
        bw = pkg.body.width.nominal
        return f"{pkg.family}_{bl:.1f}x{bw:.1f}_{result.density}"
