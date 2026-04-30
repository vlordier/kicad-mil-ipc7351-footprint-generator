# SPDX-License-Identifier: GPL-3.0-or-later
"""Tolerance data type — tracks nominal value with optional asymmetric bounds."""

from __future__ import annotations

from dataclasses import dataclass

_UNSET = object()


@dataclass(init=False)
class Tolerance:
    nominal: float
    plus: float = 0.0
    minus: float = 0.0
    unit: str = "mm"

    def __init__(self, nominal, plus=_UNSET, minus=_UNSET, unit="mm"):
        self.nominal = nominal
        self.unit = unit
        if plus is _UNSET and minus is _UNSET and nominal != 0.0:
            self.plus = nominal * 0.1
            self.minus = nominal * 0.1
        else:
            self.plus = 0.0 if plus is _UNSET else plus
            self.minus = 0.0 if minus is _UNSET else minus

    @property
    def max_value(self) -> float:
        return self.nominal + self.plus

    @property
    def min_value(self) -> float:
        return self.nominal - self.minus

    @property
    def range(self) -> float:
        return self.plus + self.minus

    @property
    def is_symmetric(self) -> bool:
        return abs(self.plus - self.minus) < 1e-9
