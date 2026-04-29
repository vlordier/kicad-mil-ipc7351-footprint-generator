# kicad-mil-ipc7351-footprint-generator

**CLI tool for generating IPC-7351C KiCad footprints with MIL-grade derating.**

A free alternative to **PCB Footprint Expert** for batch-generating KiCad
footprints from the command line. Designed for defense/aerospace teams
who need auditable, MIL-compliant land patterns.

![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Tests](https://img.shields.io/badge/tests-142%20passing-brightgreen)

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
- **Tolerance stacking:** Nominal, Min/Max, RSS, Worst-Case
- **All KiCad layers:** F.Cu + F.Paste + F.Mask + F.CrtYd + F.SilkS + F.Fab
- **THT gets F.Cu + B.Cu** (correct layer stack)
- **Zero runtime dependencies** beyond numpy (optional: pandas for Excel, reportlab for PDF)

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
  --library       Library name for batch output
  -o, --output    Output .kicad_mod path (auto-named if omitted)
```

### Batch Mode

```bash
cat > parts.csv << EOF
reference,value,family,length,width,lead_count,pitch,density,mil
C1,10uF,chip,3.2,1.6,0,0,A,no
U1,OpAmp,soic,5.0,4.0,8,1.27,B,yes
R1,1k,chip,1.6,0.8,0,0,C,no
EOF
kicad-mil-fpgen --batch parts.csv -o ./my_lib
```

## API

```python
from kicad_mil_fpgen.core.families import calculate, apply_mil_derating
from kicad_mil_fpgen.core.ipc7351 import PackageDefinition, BodyDimensions, Tolerance
from kicad_mil_fpgen.export.kicad_mod import KiCadModExporter

pkg = PackageDefinition(family="chip",
    body=BodyDimensions(length=Tolerance(3.2), width=Tolerance(1.6), height=Tolerance(0.55)))
result = calculate(pkg, density="A")
result = apply_mil_derating(result)
KiCadModExporter(result).export("footprint.kicad_mod")
```

## Installing

```bash
pip install -e .
# Optional:
pip install -e ".[excel]"   # for pandas-based Excel import
pip install -e ".[report]"  # for PDF calculation reports
pip install -e ".[dev]"     # for running tests
```

## Tests

```bash
pip install -e ".[dev]"
pytest tests/ -q
# 142 passed
```

## Project Structure

```
src/kicad_mil_fpgen/
├── __main__.py          # CLI entry point
├── core/
│   ├── families.py      # 4 package calculators + dispatch
│   ├── ipc7351.py       # Data models
│   ├── constants.py     # Factor tables + enums
│   ├── tolerances.py    # Tolerance stacking engine
│   ├── padstack.py      # PadShape enum
│   └── calculator.py    # Thin wrapper
└── export/
    ├── kicad_mod.py     # KiCad .kicad_mod exporter
    ├── report.py        # PDF report (optional)
    └── batch_import.py  # CSV batch importer
```

## License

GPL-3.0-or-later
