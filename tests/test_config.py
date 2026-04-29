# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the configuration system."""

import tempfile
from pathlib import Path

import pytest
import yaml

from kicad_mil_fpgen.config.manager import ConfigManager, ProfileConfig, OutputConfig, NamingConfig


class TestConfigDefaults:
    """Built-in defaults must always be loadable."""

    def test_defaults_load(self):
        config = ConfigManager()
        assert config.list_profiles() != []
        assert "mil_standard" in config.list_profiles()
        assert "nominal" in config.list_profiles()

    def test_default_profile_mil(self):
        config = ConfigManager()
        profile = config.get_profile("mil_standard")
        assert profile is not None
        assert profile.density == "A"
        assert profile.mil_derating is True

    def test_default_profile_nominal(self):
        config = ConfigManager()
        profile = config.get_profile("nominal")
        assert profile is not None
        assert profile.density == "B"

    def test_default_profile_high_density(self):
        config = ConfigManager()
        profile = config.get_profile("high_density")
        assert profile is not None
        assert profile.density == "C"

    def test_default_output_config(self):
        config = ConfigManager()
        assert config.output.format == "kicad_mod"
        assert config.output.kicad_version == "20240101"

    def test_default_naming_config(self):
        config = ConfigManager()
        assert config.naming.style == "ipc7351"
        assert config.naming.include_density is True


class TestConfigApplyProfile:
    """Applying profiles with overrides."""

    def test_apply_mil_standard(self):
        config = ConfigManager()
        settings = config.apply_profile("mil_standard")
        assert settings["density"] == "A"
        assert settings["mil_derating"] is True
        assert settings["generate_report"] is True

    def test_apply_nominal(self):
        config = ConfigManager()
        settings = config.apply_profile("nominal")
        assert settings["density"] == "B"
        assert settings["mil_derating"] is False

    def test_apply_with_overrides(self):
        config = ConfigManager()
        settings = config.apply_profile("nominal", density="A")
        assert settings["density"] == "A"
        assert settings["mil_derating"] is False

    def test_apply_unknown_raises(self):
        config = ConfigManager()
        with pytest.raises(ValueError, match="Unknown profile"):
            config.apply_profile("nonexistent")


class TestConfigCustomPaths:
    """Loading config from custom file paths."""

    def test_custom_config_file(self):
        custom_config = {
            "profiles": {
                "custom": {
                    "description": "Custom test profile",
                    "density": "C",
                    "mil_derating": True,
                    "tolerance_method": "rss",
                }
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(custom_config, f)
            f.flush()
            config = ConfigManager(custom_paths=[Path(f.name)])
            assert "custom" in config.list_profiles()
            profile = config.get_profile("custom")
            assert profile is not None
            assert profile.density == "C"
            assert profile.mil_derating is True
            assert profile.tolerance_method == "rss"

    def test_config_merging(self):
        base = {
            "profiles": {
                "base_profile": {"density": "A", "mil_derating": False},
            }
        }
        override = {
            "profiles": {
                "base_profile": {"mil_derating": True},
                "extra_profile": {"density": "C"},
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f1:
            yaml.dump(base, f1)
            f1.flush()
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f2:
                yaml.dump(override, f2)
                f2.flush()
                config = ConfigManager(custom_paths=[Path(f1.name), Path(f2.name)])
                assert "base_profile" in config.list_profiles()
                assert "extra_profile" in config.list_profiles()
                bp = config.get_profile("base_profile")
                assert bp.density == "A"
                assert bp.mil_derating is True


class TestConfigProfileDataclass:
    """ProfileConfig dataclass."""

    def test_profile_defaults(self):
        p = ProfileConfig(name="test")
        assert p.density == "B"
        assert p.mil_derating is False
        assert p.tolerance_method == "min_max"

    def test_profile_full(self):
        p = ProfileConfig(name="test", density="A", mil_derating=True, tolerance_method="worst_case",
                          courtyard_expansion=0.5, naming_prefix="MIL_", naming_suffix="_IPC",
                          annular_ring_extra=0.1, generate_report=True)
        assert p.density == "A"
        assert p.naming_prefix == "MIL_"
        assert p.generate_report is True


class TestOutputNamingConfig:
    """OutputConfig and NamingConfig dataclasses."""

    def test_output_defaults(self):
        o = OutputConfig()
        assert o.format == "kicad_mod"
        assert o.pretty_folders is True

    def test_naming_defaults(self):
        n = NamingConfig()
        assert n.style == "ipc7351"
        assert n.separator == "_"
