"""Tests for the padstack engine."""

from kicad_mil_fpgen.core.padstack import (
    PadstackEngine,
    PadDefinition,
    PadShape,
    PadType,
    LayerPad,
    SolderMaskExpansion,
    SolderPasteExpansion,
)


def test_bga_pad_nsmd():
    pad_d, mask_d = PadstackEngine.bga_pad(ball_diameter=0.5, pitch=0.8, nsmd=True)
    assert abs(pad_d - 0.425) < 0.001
    assert abs(mask_d - 0.525) < 0.001


def test_bga_pad_smd():
    pad_d, mask_d = PadstackEngine.bga_pad(ball_diameter=0.5, pitch=0.8, nsmd=False)
    assert abs(pad_d - 0.45) < 0.001
    assert abs(mask_d - 0.5) < 0.001


def test_annular_ring():
    ring = PadstackEngine.annular_ring_min(pad_diameter=1.0, class_=3)
    assert ring >= 0.05


def test_solder_mask_density_a():
    mask = SolderMaskExpansion.from_density("A")
    assert mask.top == 0.05


def test_solder_mask_density_c():
    mask = SolderMaskExpansion.from_density("C")
    assert mask.top == 0.1


def test_solder_paste_fine_pitch():
    paste = SolderPasteExpansion.from_pitch(pitch_mm=0.4)
    assert paste.top == -0.02


def test_solder_paste_wide_pitch():
    paste = SolderPasteExpansion.from_pitch(pitch_mm=1.27)
    assert paste.top == 0.0


def test_padstack_add_and_clear():
    engine = PadstackEngine()
    pad = PadDefinition(number=1, pad_type=PadType.SMD)
    engine.add_pad(pad)
    assert len(engine.pads) == 1
    engine.clear()
    assert len(engine.pads) == 0
