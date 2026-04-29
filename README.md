# kicad-mil-ipc7351-footprint-generator

**CLI tool for generating IPC-7351C KiCad footprints — adds +0.05mm to every pad for MIL-STD vibration resistance.**

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Tests](https://img.shields.io/badge/tests-142%20passing-brightgreen)

## What this does differently

| Feature | KiCad built-in | This tool |
|---------|---------------|-----------|
| **MIL derating** (`--mil`) | None | +0.05mm pads, +0.1mm courtyard |
| **Density A** (largest pads) | No | All families: 25% wider pads vs density C |
| **QFN thermal pad** | Manual | Auto-generated, 70% of body size |
| **THT dual-row** | Manual | DIP gets symmetric pads both sides |
| **Ball grid** | Per-part | N×N from body dimensions + ball count |
| **Batch CSV** | No | Generate 100+ footprints from one file |
| **Formula audit trail** | No | Every pad dimension recorded with formula used |

## Usage

```bash
pip install -e .

# Single footprint
kicad-mil-fpgen --package chip --body-length 3.2 --body-width 1.6 -o 1206.kicad_mod

# MIL-grade SOIC-8 (adds +0.05mm to every pad)
kicad-mil-fpgen --package soic --body-length 5.0 --body-width 4.0 \
  --lead-count 8 --lead-pitch 1.27 --mil -o soic8.kicad_mod

# Batch generate from CSV
cat > parts.csv << EOF
family,length,width,lead_count,pitch,density,mil
chip,3.2,1.6,0,0,A,no
soic,5.0,4.0,8,1.27,B,yes
chip,1.6,0.8,0,0,C,no
EOF
kicad-mil-fpgen --batch parts.csv -o ./my_lib
```

## Renders (KiCad 10.0.1)

| Chip 1206 MIL | SOIC-8 | DIP-8 | QFN-32 + pad | BGA-256 |
|:---:|:---:|:---:|:---:|:---:|
| <img src="docs/images/chip.svg" width="150"> | <img src="docs/images/soic.svg" width="150"> | <img src="docs/images/dip.svg" width="150"> | <img src="docs/images/qfn.svg" width="150"> | <img src="docs/images/bga.svg" width="180"> |

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--package` | required | chip, soic, tssop, qfp, qfn, dfn, bga, dip, axial, radial |
| `--body-length` | required | mm |
| `--body-width` | required | mm |
| `--density` | B | A (largest pads, MIL preferred), B (nominal), C (least) |
| `--lead-count` | — | leads/pins (required for soic/qfp/dip) |
| `--lead-pitch` | — | mm |
| `--mil` | off | +0.05mm to pads, +0.1mm to courtyard |
| `--batch` | — | CSV file path |
| `-o` | auto | Output path or directory for batch |

## Installing

```bash
pip install -e .            # zero deps beyond numpy
pip install -e ".[dev]"     # + pytest, hypothesis for tests
```

## Tests

```bash
pytest tests/ -q    # 142 passed
```

All footprints validated against KiCad 10.0.1 pcbnew — every file loads, parses, and renders.

## License

GPL-3.0-or-later
