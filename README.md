# kicad-mil-ipc7351-footprint-generator

**CLI tool that adds MIL-grade pad margins (+0.05mm) to IPC-7351C KiCad footprints.**

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Tests](https://img.shields.io/badge/tests-142%20passing-brightgreen)

## What's the MIL value?

Standard IPC footprints are designed for nominal assembly. For MIL-STD / IPC Class 3 / aerospace, you need:

| Requirement | What this tool does |
|-------------|-------------------|
| **Larger pads for vibration** | `--mil` adds +0.05mm to every pad dimension |
| **Extra courtyard clearance** | `--mil` adds +0.1mm to all courtyard edges |
| **Density A (maximum material)** | Largest pad geometry for maximum solder joint strength |
| **Auditable calculations** | Every dimension recorded with formula — include in MIL documentation |
| **QFN thermal pad** | Auto-generated for QFN/DFN (common in high-rel designs) |

Without `--mil`, you get standard IPC-7351C footprints (nominal). With `--mil`, every pad is 0.05mm larger — a simple, verifiable margin for vibration resistance.

## When this isn't for MIL

This tool also generates standard footprints for any package family. That's just plumbing — the MIL value is the `--mil` flag and Density A.

## Usage

```bash
pip install -e .

# MIL-grade chip footprint (density A + derating)
kicad-mil-fpgen --package chip --body-length 3.2 --body-width 1.6 \
  --density A --mil -o 1206_mil.kicad_mod

# MIL-grade SOIC-8
kicad-mil-fpgen --package soic --body-length 5.0 --body-width 4.0 \
  --lead-count 8 --lead-pitch 1.27 --density A --mil -o soic8_mil.kicad_mod

# Standard footprint (no MIL)
kicad-mil-fpgen --package soic --body-length 5.0 --body-width 4.0 \
  --lead-count 8 --lead-pitch 1.27 -o soic8.kicad_mod

# Batch from CSV
kicad-mil-fpgen --batch parts.csv -o ./my_lib
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--package` | required | chip, soic, tssop, qfp, qfn, dfn, bga, dip, axial, radial |
| `--body-length`, `--body-width` | required | mm |
| `--density` | B | **A** (MIL — largest pads), B (nominal), C (least) |
| `--mil` | off | **+0.05mm pads, +0.1mm courtyard** |
| `--lead-count`, `--lead-pitch` | — | for gullwing/THT packages |
| `--ball-diameter`, `--ball-count` | — | for BGA packages |
| `--batch` | — | CSV file path |
| `-o` | auto | Output path or directory |

## Renders (KiCad 10.0.1)

| Chip 1206 MIL (+0.05mm) | SOIC-8 MIL (+0.05mm) | QFN-32 + thermal pad | BGA-256 grid |
|:---:|:---:|:---:|:---:|
| <img src="docs/images/chip.svg" width="200"> | <img src="docs/images/soic.svg" width="200"> | <img src="docs/images/qfn.svg" width="200"> | <img src="docs/images/bga.svg" width="250"> |

## Test

```bash
pip install -e ".[dev]"
pytest tests/ -q    # 142 passed, validated against KiCad 10.0.1 pcbnew
```

## License

GPL-3.0-or-later
