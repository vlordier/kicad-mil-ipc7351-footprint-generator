# SPDX-License-Identifier: GPL-3.0-or-later
"""Entry point for kicad-mil-fpgen CLI."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .core.constants import DensityLevel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kicad-mil-fpgen",
        description="IPC-7351C MIL-grade footprint generator for KiCad",
    )
    parser.add_argument("--version", action="version", version=f"kicad-mil-fpgen v{__version__}")
    parser.add_argument("--package", type=str, help="Package family (chip, soic, qfp, bga, dip, ...)")
    parser.add_argument("--density", type=str, default="B", choices=[e.value for e in DensityLevel], help="IPC-7351 density level (default: B)")
    parser.add_argument("--body-length", type=float, help="Component body length in mm")
    parser.add_argument("--body-width", type=float, help="Component body width in mm")
    parser.add_argument("--body-height", type=float, default=0.5, help="Component body height in mm (default: 0.5)")
    parser.add_argument("--lead-count", type=int, help="Number of leads")
    parser.add_argument("--lead-pitch", type=float, help="Lead pitch in mm")
    parser.add_argument("--lead-width", type=float, default=0.3, help="Lead width in mm (default: 0.3)")
    parser.add_argument("--lead-length", type=float, default=1.0, help="Lead length in mm (default: 1.0)")
    parser.add_argument("--ball-diameter", type=float, help="BGA ball diameter in mm")
    parser.add_argument("--ball-count", type=int, help="BGA ball count")
    parser.add_argument("--output", type=Path, help="Output .kicad_mod file path")
    parser.add_argument("--mil", action="store_true", help="Apply MIL-grade derating")
    return parser


def cli_generate(args: argparse.Namespace) -> int:
    from .core.ipc7351 import IPC7351Calculator, PackageDefinition, BodyDimensions, LeadDimensions, Tolerance, ValidationError
    from .export.kicad_mod import KiCadModExporter

    if not args.package or not args.body_length or not args.body_width:
        print("Error: --package, --body-length, --body-width are required", file=sys.stderr)
        return 1

    pkg = PackageDefinition(
        family=args.package,
        body=BodyDimensions(
            length=Tolerance(args.body_length, args.body_length * 0.05, args.body_length * 0.05),
            width=Tolerance(args.body_width, args.body_width * 0.05, args.body_width * 0.05),
            height=Tolerance(args.body_height, args.body_height * 0.1, args.body_height * 0.1),
        ),
        ball_diameter=Tolerance(args.ball_diameter, 0.0, 0.0) if args.ball_diameter else None,
        ball_count=args.ball_count or 0,
    )
    if args.lead_count:
        pkg.leads = LeadDimensions(
            width=Tolerance(args.lead_width, args.lead_width * 0.1, args.lead_width * 0.1),
            length=Tolerance(args.lead_length, args.lead_length * 0.1, args.lead_length * 0.1),
            pitch=Tolerance(args.lead_pitch or 1.27, 0.0, 0.0),
            count=args.lead_count,
        )

    try:
        calc = IPC7351Calculator()
        result = calc.calculate_footprint(pkg, density=args.density)
    except ValidationError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.mil:
        result = calc.apply_mil_derating(result)

    output_path = args.output or Path(f"{pkg.family}_{args.body_length:.2f}x{args.body_width:.2f}.kicad_mod")
    KiCadModExporter(result).export(output_path)
    print(f"Generated: {output_path}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.package:
        return cli_generate(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
