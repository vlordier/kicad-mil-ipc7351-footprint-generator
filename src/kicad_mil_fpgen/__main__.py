# SPDX-License-Identifier: GPL-3.0-or-later
"""Entry point for kicad-mil-fpgen CLI.

Usage:
    kicad-mil-fpgen                          # Launch GUI
    kicad-mil-fpgen --package QFN-32 ...     # CLI generation (future)
    kicad-mil-fpgen --version                # Show version
"""

import argparse
import sys
from pathlib import Path

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kicad-mil-fpgen",
        description="IPC-7351C MIL-grade footprint generator for KiCad",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"kicad-mil-fpgen v{__version__}",
    )
    parser.add_argument(
        "--package",
        type=str,
        help="Package family (chip, soic, qfp, bga, dip, ...)",
    )
    parser.add_argument(
        "--density",
        type=str,
        default="B",
        choices=["A", "B", "C", "USER", "MANUFACTURER"],
        help="IPC-7351 density level (default: B)",
    )
    parser.add_argument(
        "--body-length",
        type=float,
        help="Component body length in mm",
    )
    parser.add_argument(
        "--body-width",
        type=float,
        help="Component body width in mm",
    )
    parser.add_argument(
        "--lead-count",
        type=int,
        help="Number of leads",
    )
    parser.add_argument(
        "--lead-pitch",
        type=float,
        help="Lead pitch in mm",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output .kicad_mod file path",
    )
    parser.add_argument(
        "--mil",
        action="store_true",
        help="Apply MIL-grade derating",
    )
    return parser


def cli_generate(args: argparse.Namespace) -> int:
    """CLI mode: generate a footprint from command-line arguments."""
    from .core.ipc7351 import IPC7351Calculator, PackageDefinition, BodyDimensions, LeadDimensions, Tolerance
    from .export.kicad_mod import KiCadModExporter

    if not args.package or not args.body_length or not args.body_width:
        print("Error: --package, --body-length, --body-width are required in CLI mode", file=sys.stderr)
        return 1

    pkg = PackageDefinition(
        family=args.package,
        body=BodyDimensions(
            length=Tolerance(args.body_length, args.body_length * 0.05, args.body_length * 0.05),
            width=Tolerance(args.body_width, args.body_width * 0.05, args.body_width * 0.05),
            height=Tolerance(1.0, 0.1, 0.1),
        ),
    )
    if args.lead_count:
        pkg.leads = LeadDimensions(
            width=Tolerance(0.3, 0.05, 0.05),
            length=Tolerance(1.0, 0.1, 0.1),
            pitch=Tolerance(args.lead_pitch or 1.27, 0.0, 0.0),
            count=args.lead_count,
        )

    calc = IPC7351Calculator(ipc_version="C")
    result = calc.calculate_footprint(pkg, density=args.density)

    if args.mil:
        result = calc.apply_mil_derating(result)

    output_path = args.output or Path(f"{pkg.family}_{args.body_length:.2f}x{args.body_width:.2f}.kicad_mod")
    exporter = KiCadModExporter(result)
    exporter.export(output_path)
    print(f"Generated: {output_path}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.package:
        return cli_generate(args)

    print(f"KiCad MIL IPC-7351 Footprint Generator v{__version__}")
    print("GUI mode not yet available. Use CLI flags:")
    print("  kicad-mil-fpgen --package chip --body-length 3.2 --body-width 1.6 --output my_fp.kicad_mod")
    return 0


if __name__ == "__main__":
    sys.exit(main())
