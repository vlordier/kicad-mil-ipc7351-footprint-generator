# SPDX-License-Identifier: GPL-3.0-or-later
"""Family registry — a plugin system for package family calculators.

Instead of if/elif chains, each family registers itself and the calculator
dispatches to the correct implementation. New families can be added by
simply creating a new FootprintFamily subclass and registering it.
"""

from __future__ import annotations

from typing import Optional

from .families.base import FootprintFamily, FamilyMetadata
from .families.chip import ChipFamily
from .families.gullwing import GullwingFamily
from .families.bga import BgaFamily
from .families.tht import ThtFamily


class _FamilyRegistry:
    """Singleton registry mapping family names/aliases to calculator classes."""

    def __init__(self) -> None:
        self._by_name: dict[str, type[FootprintFamily]] = {}
        self._by_alias: dict[str, type[FootprintFamily]] = {}

    def register(self, family_cls: type[FootprintFamily]) -> None:
        meta = family_cls.metadata
        self._by_name[meta.name.lower()] = family_cls
        self._by_name[meta.calc_type.value.lower()] = family_cls
        for alias in meta.aliases:
            self._by_alias[alias.lower()] = family_cls

    def resolve(self, family_or_alias: str) -> Optional[type[FootprintFamily]]:
        key = family_or_alias.strip().lower()
        if not key:
            return None
        return self._by_name.get(key) or self._by_alias.get(key)

    def get_all_families(self) -> list[type[FootprintFamily]]:
        seen = set()
        result = []
        for cls in self._by_name.values():
            if id(cls) not in seen:
                seen.add(id(cls))
                result.append(cls)
        return result

    @property
    def names(self) -> list[str]:
        return sorted(set(self._by_name.keys()) | set(self._by_alias.keys()))


# Global singleton
_registry = _FamilyRegistry()

# Register built-in families
_registry.register(ChipFamily)
_registry.register(GullwingFamily)
_registry.register(BgaFamily)
_registry.register(ThtFamily)


def resolve_family(family_or_alias: str) -> Optional[type[FootprintFamily]]:
    return _registry.resolve(family_or_alias)


def get_registered_families() -> list[type[FootprintFamily]]:
    return _registry.get_all_families()


def get_known_names() -> list[str]:
    return _registry.names
