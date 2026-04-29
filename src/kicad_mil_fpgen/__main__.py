# SPDX-License-Identifier: GPL-3.0-or-later
"""Entry point for kicad-mil-fpgen CLI and GUI."""

import argparse
import sys
from pathlib import Path

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kicad-mil-fpgen", description="IPC-7351C MIL-grade footprint generator for KiCad")
    p.add_argument("--version", action="version", version=f"kicad-mil-fpgen v{__version__}")
    p.add_argument("--package", type=str, help="Package family (chip, soic, bga, dip, ...)")
    p.add_argument("--density", type=str, default="B", choices=["A", "B", "C"], help="Density (default: B)")
    p.add_argument("--body-length", type=float, help="Body length in mm")
    p.add_argument("--body-width", type=float, help="Body width in mm")
    p.add_argument("--body-height", type=float, default=0.5, help="Body height (default: 0.5)")
    p.add_argument("--lead-count", type=int, help="Number of leads")
    p.add_argument("--lead-pitch", type=float, help="Lead pitch in mm")
    p.add_argument("--lead-width", type=float, default=0.3, help="Lead width (default: 0.3)")
    p.add_argument("--lead-length", type=float, default=1.0, help="Lead length (default: 1.0)")
    p.add_argument("--ball-diameter", type=float, help="BGA ball diameter")
    p.add_argument("--ball-count", type=int, help="BGA ball count")
    p.add_argument("--output", type=Path, help="Output .kicad_mod path")
    p.add_argument("--mil", action="store_true", help="Apply MIL derating")
    return p


def cli_generate(args: argparse.Namespace) -> int:
    from .core.ipc7351 import PackageDefinition, BodyDimensions, LeadDimensions, Tolerance, ValidationError
    from .core.families import calculate, apply_mil_derating
    from .export.kicad_mod import KiCadModExporter

    if not args.package or not args.body_length or not args.body_width:
        print("Error: --package, --body-length, --body-width required", file=sys.stderr)
        return 1

    pkg = PackageDefinition(
        family=args.package,
        body=BodyDimensions(length=Tolerance(args.body_length, args.body_length * 0.05, args.body_length * 0.05),
                            width=Tolerance(args.body_width, args.body_width * 0.05, args.body_width * 0.05),
                            height=Tolerance(args.body_height, args.body_height * 0.1, args.body_height * 0.1)),
        ball_diameter=Tolerance(args.ball_diameter, 0.0, 0.0) if args.ball_diameter else None,
        ball_count=args.ball_count or 0,
    )
    if args.lead_count:
        pkg.leads = LeadDimensions(width=Tolerance(args.lead_width, args.lead_width * 0.1, args.lead_width * 0.1),
                                   length=Tolerance(args.lead_length, args.lead_length * 0.1, args.lead_length * 0.1),
                                   pitch=Tolerance(args.lead_pitch or 1.27, 0.0, 0.0), count=args.lead_count)
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
    return 0


def launch_gui() -> int:
    try:
        from PySide6.QtWidgets import QApplication
        from .gui.main_window import MainWindow
    except ImportError:
        print("GUI requires PySide6", file=sys.stderr)
        return 1
    app = QApplication(sys.argv)
    app.setApplicationName("KiCad MIL IPC-7351 Footprint Generator")
    window = MainWindow()
    window.show()
    return app.exec()


def main() -> int:
    args = build_parser().parse_args()
    if args.package:
        return cli_generate(args)
    return launch_gui()


if __name__ == "__main__":
    sys.exit(main())
