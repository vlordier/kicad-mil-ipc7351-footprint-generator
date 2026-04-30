# SPDX-License-Identifier: GPL-3.0-or-later
"""Entry point for kicad-mil-fpgen CLI."""

import argparse
import sys
from pathlib import Path

from . import __version__

from .core.constants import (
    DEFAULT_BODY_HEIGHT_MM, DEFAULT_LEAD_WIDTH_MM, DEFAULT_LEAD_LENGTH_MM,
    DEFAULT_LEAD_PITCH_MM,
    BODY_LENGTH_TOLERANCE_PCT, BODY_WIDTH_TOLERANCE_PCT, BODY_HEIGHT_TOLERANCE_PCT,
    LEAD_WIDTH_TOLERANCE_PCT, LEAD_LENGTH_TOLERANCE_PCT,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kicad-mil-fpgen", description="IPC-7351C MIL-grade footprint generator for KiCad")
    p.add_argument("--version", action="version", version=f"kicad-mil-fpgen v{__version__}")
    p.add_argument("--package", type=str, required=True, help="Package family (chip, soic, bga, dip, ...)")
    p.add_argument("--density", type=str, default="B", choices=["A", "B", "C"], help="Density: A (MIL preferred), B (nominal), C (least)")
    p.add_argument("--body-length", type=float, required=True, help="Body length in mm")
    p.add_argument("--body-width", type=float, required=True, help="Body width in mm")
    p.add_argument("--body-height", type=float, default=DEFAULT_BODY_HEIGHT_MM, help="Body height in mm")
    p.add_argument("--lead-count", type=int, help="Number of leads")
    p.add_argument("--lead-pitch", type=float, help="Lead pitch in mm")
    p.add_argument("--lead-width", type=float, default=DEFAULT_LEAD_WIDTH_MM, help="Lead width in mm")
    p.add_argument("--lead-length", type=float, default=DEFAULT_LEAD_LENGTH_MM, help="Lead length in mm")
    p.add_argument("--ball-diameter", type=float, help="BGA ball diameter in mm")
    p.add_argument("--ball-count", type=int, help="BGA ball count")
    p.add_argument("--output", "-o", type=Path, help="Output .kicad_mod path")
    p.add_argument("--mil", action="store_true", help="Apply MIL derating (+0.05mm pads, +0.1mm courtyard)")
    p.add_argument("--batch", type=Path, help="CSV file for batch generation")
    p.add_argument("--library", type=str, default="generated", help="Library name for batch output (default: generated)")
    return p


def cli_generate(args: argparse.Namespace) -> int:
    from .core.ipc7351 import PackageDefinition, BodyDimensions, LeadDimensions, Tolerance, ValidationError
    from .core.families import calculate, apply_mil_derating
    from .export.kicad_mod import KiCadModExporter

    body = BodyDimensions(
        length=Tolerance(args.body_length, args.body_length * BODY_LENGTH_TOLERANCE_PCT, args.body_length * BODY_LENGTH_TOLERANCE_PCT),
        width=Tolerance(args.body_width, args.body_width * BODY_WIDTH_TOLERANCE_PCT, args.body_width * BODY_WIDTH_TOLERANCE_PCT),
        height=Tolerance(args.body_height, args.body_height * BODY_HEIGHT_TOLERANCE_PCT, args.body_height * BODY_HEIGHT_TOLERANCE_PCT),
    )
    pkg = PackageDefinition(
        family=args.package, body=body,
        ball_diameter=Tolerance(args.ball_diameter, 0.0, 0.0) if args.ball_diameter else None,
        ball_count=args.ball_count or 0,
    )
    if args.lead_count:
        pkg.leads = LeadDimensions(
            width=Tolerance(args.lead_width, args.lead_width * LEAD_WIDTH_TOLERANCE_PCT, args.lead_width * LEAD_WIDTH_TOLERANCE_PCT),
            length=Tolerance(args.lead_length, args.lead_length * LEAD_LENGTH_TOLERANCE_PCT, args.lead_length * LEAD_LENGTH_TOLERANCE_PCT),
            pitch=Tolerance(args.lead_pitch or DEFAULT_LEAD_PITCH_MM, 0.0, 0.0), count=args.lead_count,
        )
    try:
        result = calculate(pkg, density=args.density)
    except ValidationError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    if args.mil:
        result = apply_mil_derating(result)
    out = args.output or Path(f"{pkg.family}_{args.body_length:.2f}x{args.body_width:.2f}.kicad_mod")
    KiCadModExporter(result).export(out)
    print(f"Generated: {out}")
    print(f"  {len(result.pads)} pads, courtyard {result.courtyard.width:.2f}x{result.courtyard.height:.2f} mm")
    return 0


def cli_batch(args: argparse.Namespace) -> int:
    from .export.batch_import import BatchImporter
    try:
        importer = BatchImporter(args.output or Path.cwd(), library_name=args.library)
        result = importer.from_csv(args.batch)
        print(f"Batch: {result.succeeded}/{result.total} succeeded, {result.failed} failed")
        for row, err in result.errors:
            print(f"  Row {row}: {err}", file=sys.stderr)
        return 0 if result.failed == 0 else 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    args = build_parser().parse_args()
    if args.batch:
        return cli_batch(args)
    return cli_generate(args)


if __name__ == "__main__":
    sys.exit(main())
