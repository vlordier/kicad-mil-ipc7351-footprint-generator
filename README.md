# kicad-mil-ipc7351-footprint-generator

**CLI tool that adds +0.05mm to every pad for MIL-STD vibration-resistant KiCad footprints.**

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Tests](https://img.shields.io/badge/tests-151%20passing-brightgreen)

## The MIL part

Standard IPC-7351 footprints are designed for nominal assembly. For MIL-STD / IPC Class 3:

| What | What this tool does |
|------|-------------------|
| `--mil` flag | Adds exactly **+0.05mm** to every pad width and height |
| | Adds exactly **+0.1mm** to every courtyard edge |
| `--density A` | Uses the **maximum material** density level — largest IPC-permitted pads |

Without `--mil` you get standard IPC-7351C footprints. With `--mil` every pad is 0.05mm larger — a simple, verifiable, auditable margin.

## The non-MIL part (just standard footprint generation)

This tool also generates standard footprints for chip, SOIC, QFP, QFN, BGA, DIP, and axial packages. That's table stakes — every footprint generator does this. The renders below show the package support, not MIL features.

| Chip 1206 | SOIC-8 | QFN-32 w/ pad | BGA-256 |
|:---:|:---:|:---:|:---:|
| <img src="docs/images/chip.svg" width="180"> | <img src="docs/images/soic.svg" width="180"> | <img src="docs/images/qfn.svg" width="180"> | <img src="docs/images/bga.svg" width="220"> |

## Usage

```bash
pip install -e .

# MIL-grade (adds +0.05mm to pads)
kicad-mil-fpgen --package chip --body-length 3.2 --body-width 1.6 \
  --density A --mil -o 1206_mil.kicad_mod

# Standard (no MIL derating)
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
| `--density` | B | **A** (largest pads), B (nominal), C (least) |
| `--mil` | off | **+0.05mm pads, +0.1mm courtyard** |
| `--lead-count`, `--lead-pitch` | — | for gullwing/THT packages |
| `--ball-diameter`, `--ball-count` | — | for BGA packages |
| `--batch` | — | CSV file path |
| `-o` | auto | Output path or directory |

## Test

```bash
pip install -e ".[dev]"
pytest tests/ -q    # 151 passed, validated against KiCad 10.0.1 pcbnew
```

## License

GPL-3.0-or-later
