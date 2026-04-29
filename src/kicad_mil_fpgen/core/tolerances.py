# SPDX-License-Identifier: GPL-3.0-or-later
"""Tolerance stacking engine per J-STD-001 and IPC-7351.

Supports nominal, min/max, RSS, and worst-case tolerance stacking methods.
All calculations are transparent for PDF report documentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import math


class ToleranceMethod(Enum):
    NOMINAL = "nominal"
    MIN_MAX = "min_max"
    RSS = "rss"
    WORST_CASE = "worst_case"


@dataclass
class Tolerance:
    nominal: float
    plus: float = 0.0
    minus: float = 0.0
    unit: str = "mm"

    def __post_init__(self):
        if self.minus == 0.0 and self.plus == 0.0:
            self.minus = self.nominal * 0.1
            self.plus = self.nominal * 0.1

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


@dataclass
class ToleranceStackResult:
    nominal: float = 0.0
    min: float = 0.0
    max: float = 0.0
    plus: float = 0.0
    minus: float = 0.0
    method: ToleranceMethod = ToleranceMethod.NOMINAL


@dataclass
class ToleranceStack:
    tolerances: list[Tolerance] = field(default_factory=list)
    method: ToleranceMethod = ToleranceMethod.NOMINAL

    def add(self, tol: Tolerance) -> None:
        self.tolerances.append(tol)

    def compute(self) -> ToleranceStackResult:
        result = ToleranceStackResult()
        result.method = self.method

        if not self.tolerances:
            return result

        if self.method == ToleranceMethod.WORST_CASE:
            return self._worst_case()
        elif self.method == ToleranceMethod.RSS:
            return self._rss()
        else:
            return self._min_max()

    def _min_max(self) -> ToleranceStackResult:
        result = ToleranceStackResult(method=self.method)
        total_nominal = sum(t.nominal for t in self.tolerances)
        total_min = sum(t.min_value for t in self.tolerances)
        total_max = sum(t.max_value for t in self.tolerances)

        result.nominal = total_nominal
        result.min = total_min
        result.max = total_max
        result.minus = total_nominal - total_min
        result.plus = total_max - total_nominal
        return result

    def _rss(self) -> ToleranceStackResult:
        result = ToleranceStackResult(method=self.method)
        total_nominal = sum(t.nominal for t in self.tolerances)
        rss_plus = math.sqrt(sum(t.plus ** 2 for t in self.tolerances))
        rss_minus = math.sqrt(sum(t.minus ** 2 for t in self.tolerances))

        result.nominal = total_nominal
        result.min = total_nominal - rss_minus
        result.max = total_nominal + rss_plus
        result.minus = rss_minus
        result.plus = rss_plus
        return result

    def _worst_case(self) -> ToleranceStackResult:
        result = ToleranceStackResult(method=self.method)
        total_nominal = sum(t.nominal for t in self.tolerances)
        total_plus = sum(t.plus for t in self.tolerances)
        total_minus = sum(t.minus for t in self.tolerances)
        result.nominal = total_nominal
        result.min = total_nominal - total_minus
        result.max = total_nominal + total_plus
        result.minus = total_minus
        result.plus = total_plus
        return result


class ToleranceEngine:
    """Factory and utility for tolerance operations."""

    @staticmethod
    def from_nominal(nominal: float, percent: float = 10.0) -> Tolerance:
        tol = nominal * percent / 100.0
        return Tolerance(nominal=nominal, plus=tol, minus=tol)

    @staticmethod
    def stack(
        tolerances: list[Tolerance],
        method: ToleranceMethod = ToleranceMethod.MIN_MAX,
    ) -> ToleranceStackResult:
        stack = ToleranceStack(tolerances=tolerances, method=method)
        return stack.compute()

    @staticmethod
    def solder_fillet(
        lead_thickness: float,
        pad_length: float,
        class_: int = 3,
    ) -> tuple[float, float]:
        """Calculate J-STD-001 solder fillet dimensions.

        Returns (toe_fillet, heel_fillet) in mm.
        """
        toe_min = max(0.2, lead_thickness * 0.5)
        heel_min = max(0.1, pad_length * 0.25)

        if class_ >= 3:
            toe_min = max(0.3, lead_thickness * 0.75)
            heel_min = max(0.15, pad_length * 0.3)

        return (toe_min, heel_min)
