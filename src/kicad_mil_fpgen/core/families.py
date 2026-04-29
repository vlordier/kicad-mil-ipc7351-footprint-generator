# SPDX-License-Identifier: GPL-3.0-or-later
"""Package family calculators — dispatched by family name."""

from __future__ import annotations

import copy
import math

from .constants import FAMILY_FACTORS, FAMILY_KEY_MAP, ANNULAR_RING_BASE
from .constants import MIL_PAD_INCREMENT, MIL_COURTYARD_INCREMENT
from .ipc7351 import (
    PackageDefinition, FootprintResult, PadDimensions, PadPosition, PadShape,
    Courtyard, FootprintError, ValidationError,
)


def _get_factors(family: str, density: str) -> dict:
    key = FAMILY_KEY_MAP.get(family.lower().strip(), "chip")
    table = FAMILY_FACTORS.get(key, FAMILY_FACTORS["chip"])
    return table.get(density.upper(), table.get("B", table["B"]))


def _record(result: FootprintResult, name: str, formula: str, *args) -> None:
    detail = f"{formula} = {[f'{a:.4f}' if isinstance(a, float) else a for a in args]}"
    result.formulas_used[name] = detail


def _calc_courtyard(pkg: PackageDefinition, factors: dict, result: FootprintResult) -> None:
    cy_exp = factors.get("courtyard", 0.25)
    if result.pads:
        xs, ys = [], []
        for p in result.pads:
            xs.extend([p.position.x - p.width / 2, p.position.x + p.width / 2])
            ys.extend([p.position.y - p.height / 2, p.position.y + p.height / 2])
        x_min, x_max = min(xs) - cy_exp, max(xs) + cy_exp
        y_min, y_max = min(ys) - cy_exp, max(ys) + cy_exp
    else:
        if pkg.body is None:
            raise FootprintError("Cannot compute courtyard")
        bl, bw = pkg.body.length.nominal, pkg.body.width.nominal
        x_min, x_max = -bl / 2 - cy_exp, bl / 2 + cy_exp
        y_min, y_max = -bw / 2 - cy_exp, bw / 2 + cy_exp

    result.courtyard = Courtyard(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
                                  assembly_expansion=cy_exp, silkscreen_expansion=cy_exp)
    result.formulas_used["courtyard"] = f"CY = PadExtent + 2*CY_exp = {x_max - x_min:.4f}"


def _calc_chip(pkg: PackageDefinition, factors: dict, result: FootprintResult) -> None:
    body = pkg.body
    if body is None:
        raise FootprintError("Body required for chip")
    f = factors
    bl, bw = body.length.nominal, body.width.nominal
    pw = bw + 2 * f["side"]
    ph = bl + f["toe"] + f["heel"]
    cx = bl / 2 + (f["toe"] - f["heel"]) / 2
    result.pads.append(PadDimensions(number=1, width=pw, height=ph, toe=f["toe"], heel=f["heel"], side=f["side"],
                                      shape=PadShape.ROUNDED_RECTANGLE, position=PadPosition(x=-cx, y=0.0)))
    result.pads.append(PadDimensions(number=2, width=pw, height=ph, toe=f["toe"], heel=f["heel"], side=f["side"],
                                      shape=PadShape.ROUNDED_RECTANGLE, position=PadPosition(x=cx, y=0.0)))
    _record(result, "chip_pad_width", "W = B + 2S", bw, f["side"], pw)
    _record(result, "chip_pad_height", "L = T + H + Toe", bl, f["toe"], f["heel"], ph)
    result.notes.append(f"Chip — pad W={pw:.3f} H={ph:.3f}, 2 pads at ±{cx:.3f}")


def _calc_gullwing(pkg: PackageDefinition, factors: dict, result: FootprintResult) -> None:
    body, leads = pkg.body, pkg.leads
    if body is None or leads is None:
        raise FootprintError("Body and leads required for gullwing")
    f = factors
    lw, ll = leads.width.nominal, leads.length.nominal
    pitch, count = leads.pitch.nominal, leads.count
    pw = lw + 2 * f["side"]
    ph = ll + f["toe"] + f["heel"]
    pps = count // 2
    span = (pps - 1) * pitch
    overhang = (ph - ll) / 2
    pn = 1
    for i in range(pps):
        y = -span / 2 + i * pitch
        result.pads.append(PadDimensions(number=pn, width=pw, height=ph, toe=f["toe"], heel=f["heel"], side=f["side"],
                                          shape=PadShape.OBLONG, position=PadPosition(x=-(body.length.nominal / 2 + overhang), y=y)))
        pn += 1
        result.pads.append(PadDimensions(number=pn, width=pw, height=ph, toe=f["toe"], heel=f["heel"], side=f["side"],
                                          shape=PadShape.OBLONG, position=PadPosition(x=body.length.nominal / 2 + overhang, y=y)))
        pn += 1

    if pkg.family.lower() in ("qfn", "dfn"):
        tw = body.width.nominal * 0.7
        th = body.length.nominal * 0.7
        result.pads.append(PadDimensions(number=pn, width=tw, height=th, shape=PadShape.ROUNDED_RECTANGLE,
                                          corner_radius=0.2, position=PadPosition(x=0.0, y=0.0), notes=["Thermal pad"]))
        result.notes.append(f"  Thermal pad: {tw:.3f} x {th:.3f} mm")

    _record(result, "gullwing_pad_width", "W = LW + 2S", lw, f["side"], pw)
    _record(result, "gullwing_pad_height", "L = LL + Toe + Heel", ll, f["toe"], f["heel"], ph)
    result.notes.append(f"Gull-wing — {count} leads, pitch={pitch:.3f}, pad W={pw:.3f} H={ph:.3f}")


def _calc_bga(pkg: PackageDefinition, factors: dict, result: FootprintResult) -> None:
    if pkg.ball_diameter is None:
        raise FootprintError("Ball diameter required for BGA")
    bd = pkg.ball_diameter.nominal
    pd = bd * factors.get("nsmd_ratio", 0.85)
    n = max(pkg.ball_count, 1)
    side = int(math.ceil(math.sqrt(n)))
    rows = cols = side
    while rows * cols < n:
        rows += 1 if rows <= cols else cols + 1
    pitch = 0.75
    if pkg.body and pkg.body.length.nominal > 0 and pkg.body.width.nominal > 0:
        pitch = math.sqrt(pkg.body.length.nominal * pkg.body.width.nominal / n) * 0.85

    xs = -(cols - 1) * pitch / 2
    ys = -(rows - 1) * pitch / 2
    pn = 1
    for r in range(rows):
        for c in range(cols):
            if pn > n:
                break
            result.pads.append(PadDimensions(number=pn, width=pd, height=pd, shape=PadShape.CIRCLE,
                                              position=PadPosition(x=xs + c * pitch, y=ys + r * pitch)))
            pn += 1
    result.notes.append(f"BGA — {n} balls ({rows}x{cols}), pitch={pitch:.3f}, pad dia={pd:.3f}")


def _calc_tht(pkg: PackageDefinition, factors: dict, result: FootprintResult) -> None:
    body, leads = pkg.body, pkg.leads
    if body is None or leads is None:
        raise FootprintError("Body and leads required for THT")
    ld = leads.width.nominal
    annulus = factors.get("annular_extra", 0.1) + ANNULAR_RING_BASE
    pd = ld + 2 * annulus
    pitch, count = leads.pitch.nominal, leads.count
    dual = pkg.family.lower() == "dip"
    half = count // 2 if dual else count
    cols = [-(body.length.nominal / 2 + pd / 2), body.length.nominal / 2 + pd / 2] if dual else [body.length.nominal / 2 + pd / 2]
    pn = 1
    for side_x in cols:
        span = (half - 1) * pitch
        for i in range(half):
            y = -span / 2 + i * pitch
            result.pads.append(PadDimensions(number=pn, width=pd, height=pd, shape=PadShape.CIRCLE,
                                              notes=[f"Annular ring = {annulus:.3f} mm"],
                                              position=PadPosition(x=side_x, y=y)))
            pn += 1
    result.notes.append(f"THT — lead dia={ld:.3f}, pad dia={pd:.3f}")


# Dispatch table
FAMILY_DISPATCH: dict[str, tuple] = {
    "chip": (_calc_chip, False, False),
    "gullwing": (_calc_gullwing, True, False),
    "bga": (_calc_bga, False, True),
    "tht": (_calc_tht, True, False),
}


def calculate(pkg: PackageDefinition, density: str = "B") -> FootprintResult:
    pkg.validate()
    factors = _get_factors(pkg.family, density)
    key = FAMILY_KEY_MAP.get(pkg.family.lower().strip(), "chip")
    calc_fn, needs_leads, needs_ball = FAMILY_DISPATCH.get(key, (None, False, False))

    if calc_fn is None:
        raise ValidationError(f"Unknown package family: {pkg.family}")
    if needs_leads and pkg.leads is None:
        raise ValidationError(f"{pkg.family} requires lead dimensions")
    if needs_ball and pkg.ball_diameter is None:
        raise ValidationError(f"{pkg.family} requires ball diameter")

    result = FootprintResult(package=pkg, density=density.upper())
    calc_fn(pkg, factors, result)
    _calc_courtyard(pkg, factors, result)
    return result


def apply_mil_derating(result: FootprintResult) -> FootprintResult:
    mil = copy.deepcopy(result)
    for pad in mil.pads:
        pad.width += MIL_PAD_INCREMENT
        pad.height += MIL_PAD_INCREMENT
        pad.notes.append(f"MIL derating: +{MIL_PAD_INCREMENT}mm added")
    if mil.courtyard:
        mil.courtyard.x_min -= MIL_COURTYARD_INCREMENT
        mil.courtyard.x_max += MIL_COURTYARD_INCREMENT
        mil.courtyard.y_min -= MIL_COURTYARD_INCREMENT
        mil.courtyard.y_max += MIL_COURTYARD_INCREMENT
        mil.courtyard.notes.append(f"MIL derating: extra {MIL_COURTYARD_INCREMENT}mm courtyard")
    mil.notes.append("MIL derating applied (vibration-resistant)")
    return mil
