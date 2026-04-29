# kicad-mil-ipc7351-footprint-generator

**CLI tool for generating IPC-7351C KiCad footprints with MIL-grade derating.**

![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Tests](https://img.shields.io/badge/tests-142%20passing-brightgreen)

## Renders (KiCad 10.0.1)

| Chip 1206 MIL | SOIC-8 | DIP-8 |
|:---:|:---:|:---:|
| <img src="docs/images/chip.svg" width="200"> | <img src="docs/images/soic.svg" width="200"> | <img src="docs/images/dip.svg" width="200"> |

| QFN-32 + thermal pad | BGA-256 |
|:---:|:---:|
| <img src="docs/images/qfn.svg" width="300"> | <img src="docs/images/bga.svg" width="400"> |

## Who is this for?

**This tool is useful if:**

- You need to **generate 50+ footprints from a BOM** and don't want to click through KiCad's wizard that many times. The batch CSV import handles this.
- You're doing **MIL-STD / IPC Class 3 work** and want the `--mil` flag to automatically add vibration-resistant pad margins (+0.05mm pads, +0.1mm courtyard).
- You need **auditable footprint calculations** — every dimension is `body_width + 2*side` recorded with the formula used, so you can include it in design documentation.
- You want **non-standard component sizes** that aren't in KiCad's built-in wizard. Enter any body dimensions, get a valid footprint.

**This tool is NOT useful if:**

- You need one or two footprints for common parts (0805, SOIC-8, etc.) — KiCad's own footprint wizard does this faster.
- You need 3D models, pattern wizards, or fab house integration — use PCB Footprint Expert (paid) or KiCad's library.
- You want a GUI — there is no GUI. This is a command-line tool.

## Quick Start

```bash
pip install -e .
kicad-mil-fpgen --package chip --body-length 3.2 --body-width 1.6 -o 1206.kicad_mod
kicad-mil-fpgen --package soic --body-length 5.0 --body-width 4.0 \
  --lead-count 8 --lead-pitch 1.27 -o soic8.kicad_mod
kicad-mil-fpgen --package dip --body-length 9.3 --body-width 6.4 \
  --lead-count 8 --lead-pitch 2.54 -o dip8.kicad_mod --mil
```

## Features

- **4 package families:** Chip, Gullwing (SOIC/QFP/QFN), BGA, Through-hole (DIP/axial)
- **3 density levels:** A (MIL preferred, largest pads), B (nominal), C (least)
- **`--mil` flag:** +0.05mm pads, +0.1mm courtyard for vibration resistance
- **Full ball grid** for BGA (N×N from body dimensions)
- **QFN thermal pad** auto-generated under body
- **THT dual-row** for DIP (pads on both sides)
- **Batch CSV import** `kicad-mil-fpgen --batch parts.csv`
- **All KiCad layers:** F.Cu + F.Paste + F.Mask + F.CrtYd + F.SilkS + F.Fab
- **Zero runtime dependencies** beyond numpy

## Batch Mode

```bash
cat > parts.csv << EOF
reference,value,family,length,width,lead_count,pitch,density,mil
C1,10uF,chip,3.2,1.6,0,0,A,no
U1,OpAmp,soic,5.0,4.0,8,1.27,B,yes
R1,1k,chip,1.6,0.8,0,0,C,no
EOF
kicad-mil-fpgen --batch parts.csv -o ./my_lib
```

## Usage

```bash
kicad-mil-fpgen --package <family> --body-length <mm> --body-width <mm> [options]

Options:
  --package       chip, soic, tssop, qfp, qfn, dfn, bga, dip, axial, radial
  --density       A | B | C  (default: B)
  --body-length   Body length in mm (required)
  --body-width    Body width in mm (required)
  --lead-count    Number of leads (required for soic/qfp/dip)
  --lead-pitch    Lead pitch in mm
  --mil           Apply MIL derating
  --batch         CSV file for batch processing
  -o, --output    Output .kicad_mod path (auto-named if omitted)
```

## Installing

```bash
pip install -e .
pip install -e ".[dev]"     # for running tests
```

## Tests

```bash
pip install -e ".[dev]"
pytest tests/ -q
# 142 passed
All footprints validated against KiCad 10.0.1 pcbnew — every file loads, parses, and renders correctly.
```

## License

GPL-3.0-or-later
