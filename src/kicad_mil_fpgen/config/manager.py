# SPDX-License-Identifier: GPL-3.0-or-later
"""Configuration management — hierarchical YAML config with profile support.

Config layers (lowest to highest priority):
  1. Built-in defaults (config/defaults.yaml)
  2. System-wide (~/.config/kicad-mil-fpgen/config.yaml or $XDG_CONFIG_HOME)
  3. Project-local (.kicad-mil-fpgen.yaml in CWD)
  4. Environment variables (KICAD_MIL_FPGEN_*)
  5. CLI flags (highest priority)

Profiles group settings for common use cases (MIL, nominal, high-density).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import yaml


@dataclass
class ProfileConfig:
    """Named profile with pre-configured settings."""
    name: str = ""
    description: str = ""
    density: str = "B"
    mil_derating: bool = False
    tolerance_method: str = "min_max"
    courtyard_expansion: float = 0.25
    naming_prefix: str = ""
    naming_suffix: str = ""
    annular_ring_extra: float = 0.0
    generate_report: bool = False


@dataclass
class OutputConfig:
    format: str = "kicad_mod"
    kicad_version: str = "20240101"
    generator_name: str = "kicad-mil-ipc7351"
    library_prefix: str = ""
    pretty_folders: bool = True


@dataclass
class NamingConfig:
    style: str = "ipc7351"
    include_density: bool = True
    include_version: bool = True
    separator: str = "_"


def _dict_to_profile(name: str, d: dict) -> ProfileConfig:
    return ProfileConfig(
        name=name,
        description=d.get("description", ""),
        density=d.get("density", "B"),
        mil_derating=d.get("mil_derating", False),
        tolerance_method=d.get("tolerance_method", "min_max"),
        courtyard_expansion=d.get("courtyard_expansion", 0.25),
        naming_prefix=d.get("naming_prefix", ""),
        naming_suffix=d.get("naming_suffix", ""),
        annular_ring_extra=d.get("annular_ring_extra", 0.0),
        generate_report=d.get("generate_report", False),
    )


def _find_config_paths() -> list[Path]:
    paths = []

    # 1. Built-in defaults
    pkg_dir = Path(__file__).resolve().parent
    defaults = pkg_dir / "defaults.yaml"
    if defaults.exists():
        paths.append(defaults)

    # 2. System-wide config
    xdg_config = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    system_config = Path(xdg_config) / "kicad-mil-fpgen" / "config.yaml"
    if system_config.exists():
        paths.append(system_config)

    # 3. Project-local config
    local_config = Path.cwd() / ".kicad-mil-fpgen.yaml"
    if local_config.exists():
        paths.append(local_config)

    return paths


class ConfigManager:
    """Loads and merges configuration from all sources."""

    def __init__(self, custom_paths: Optional[list[Path]] = None) -> None:
        self._raw: dict[str, Any] = {}
        self._profiles: dict[str, ProfileConfig] = {}
        self.output: OutputConfig = OutputConfig()
        self.naming: NamingConfig = NamingConfig()
        self._load(custom_paths)

    def _load(self, custom_paths: Optional[list[Path]] = None) -> None:
        sources = custom_paths if custom_paths is not None else _find_config_paths()

        merged: dict[str, Any] = {}
        for path in sources:
            if path.exists():
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
                    merged = self._deep_merge(merged, data)

        self._raw = merged

        # Parse profiles
        profiles_raw = merged.get("profiles", {})
        for name, data in profiles_raw.items():
            if isinstance(data, dict):
                self._profiles[name] = _dict_to_profile(name, data)

        # Parse output config
        out_raw = merged.get("output", {})
        self.output = OutputConfig(**{k: v for k, v in out_raw.items() if k in OutputConfig.__dataclass_fields__})

        # Parse naming config
        naming_raw = merged.get("naming", {})
        self.naming = NamingConfig(**{k: v for k, v in naming_raw.items() if k in NamingConfig.__dataclass_fields__})

    def get_profile(self, name: str) -> Optional[ProfileConfig]:
        return self._profiles.get(name)

    def list_profiles(self) -> list[str]:
        return list(self._profiles.keys())

    def apply_profile(self, profile_name: str, **overrides) -> dict[str, Any]:
        profile = self.get_profile(profile_name)
        if profile is None:
            raise ValueError(f"Unknown profile: {profile_name}. Available: {self.list_profiles()}")
        result = {
            "density": profile.density,
            "mil_derating": profile.mil_derating,
            "tolerance_method": profile.tolerance_method,
            "courtyard_expansion": profile.courtyard_expansion,
            "naming_prefix": profile.naming_prefix,
            "naming_suffix": profile.naming_suffix,
            "annular_ring_extra": profile.annular_ring_extra,
            "generate_report": profile.generate_report,
        }
        result.update(overrides)
        return result

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        result = base.copy()
        for key, val in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(val, dict):
                result[key] = ConfigManager._deep_merge(result[key], val)
            else:
                result[key] = val
        return result
