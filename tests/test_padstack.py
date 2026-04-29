# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the PadShape enum."""

from kicad_mil_fpgen.core.padstack import PadShape


def test_pad_shape_values():
    assert PadShape.RECTANGLE.value == "rect"
    assert PadShape.ROUNDED_RECTANGLE.value == "rounded_rect"
    assert PadShape.OBLONG.value == "oblong"
    assert PadShape.CIRCLE.value == "circle"
    assert PadShape.CUSTOM.value == "custom"


def test_pad_shape_unicity():
    values = [s.value for s in PadShape]
    assert len(values) == len(set(values))
