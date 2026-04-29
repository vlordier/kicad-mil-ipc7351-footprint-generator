# SPDX-License-Identifier: GPL-3.0-or-later
"""Pad shape enum used across the footprint generator."""

from enum import Enum


class PadShape(Enum):
    RECTANGLE = "rect"
    ROUNDED_RECTANGLE = "rounded_rect"
    OBLONG = "oblong"
    CIRCLE = "circle"
    CUSTOM = "custom"
