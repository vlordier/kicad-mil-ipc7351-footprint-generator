# kicad-mil-ipc7351-footprint-generator

**Open-source, state-of-the-art IPC-7351C footprint generator for KiCad focused on MIL-STD, aerospace, and high-reliability applications.**

A free alternative to **PCB Footprint Expert (Library Expert)** that produces production-ready, MIL-grade footprints with full tolerance stacking, J-STD-001 compliance, and high-reliability presets.

![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

---

## Features

- Full **IPC-7351B / IPC-7351C** and **IPC-7352** compliance
- 5 density levels: **Density A (Most – MIL preferred)**, B, C, User, Manufacturer
- Advanced tolerance handling (Nominal + Tol, Min/Max stacking)
- Rounded, oblong, D-shaped, and custom pad geometries
- Automatic solder paste & mask expansions per J-STD-001
- MIL/high-reliability presets (larger fillets, stricter courtyard, vibration-resistant pads)
- Padstack editor with multi-layer support
- Batch generation from CSV / Excel
- Live 2D preview + optional 3D
- Full KiCad v6/v7/v8 `.kicad_mod` + `.pretty` library output
- Automatic PDF calculation report (great for design reviews and MIL documentation)

## Why This Project Exists

Commercial tools like PCB Library Expert are excellent but expensive and closed-source. This project aims to provide the **high-reliability community** (defense, aerospace, medical, space) with a transparent, auditable, and free tool that meets or exceeds MIL-PRF and IPC Class 3 requirements.

---

## Installation

### Option 1: Pre-built Installers (Recommended)

Download the latest release for your OS:
- Windows: `.exe` installer
- Linux: `.AppImage` or `.deb`
- macOS: `.dmg`

### Option 2: From Source

```bash
git clone https://github.com/YOURNAME/kicad-mil-ipc7351-footprint-generator.git
cd kicad-mil-ipc7351-footprint-generator
pip install -e .
kicad-mil-fpgen
```

### Requirements

- Python 3.11+
- KiCad 6, 7, or 8

---

## Quick Start

1. Launch the application (`kicad-mil-fpgen`)
2. Choose package family → Enter dimensions (or load datasheet values)
3. Select **Density A (MIL)** profile
4. Click **Generate**
5. Export to your KiCad library

---

## Repository Structure

```
kicad-mil-ipc7351-footprint-generator/
├── src/
│   └── kicad_mil_fpgen/
│       ├── __init__.py
│       ├── __main__.py
│       ├── core/            # IPC calculation engine
│       │   ├── ipc7351.py
│       │   ├── padstack.py
│       │   └── tolerances.py
│       ├── gui/             # PySide6 interface
│       │   ├── main_window.py
│       │   ├── wizard.py
│       │   └── preview.py
│       ├── models/          # Data models
│       │   ├── package.py
│       │   └── component.py
│       └── export/          # Output generators
│           ├── kicad_mod.py
│           └── report.py
├── ipc_data/                # IPC tables & formulas (YAML/JSON)
│   ├── tables/
│   └── formulas.yaml
├── templates/               # MIL presets & user templates
│   └── mil_grade_A.yaml
├── tests/
├── docs/
├── resources/
│   └── icons/
├── pyproject.toml
└── README.md
```

---

## Comparison: Kicad MIL IPC7351 vs PCB Footprint Expert

| Feature | PCB Footprint Expert | Kicad MIL IPC7351 |
|---------|---------------------|-------------------|
| License | Commercial / Paid | **Free (GPLv3)** |
| IPC-7351C | ✓ | ✓ |
| Density Levels | 3 | **5 (incl. MIL presets)** |
| Tolerance Stacking | Nominal only | **Nominal, Min/Max, RSS, Worst-Case** |
| MIL Presets | ✗ | **Built-in** |
| PDF Calculation Report | Limited | **Full (all formulas transparent)** |
| Batch Generation | ✓ | ✓ |
| Cross-Platform | Windows only | **Windows, Linux, macOS** |
| 2D Preview | ✓ | ✓ |
| KiCad Plugin | ✗ | **Planned** |
| CLI Mode | ✗ | **Planned** |

---

## MIL / High-Reliability Usage Guide

For high-reliability designs (MIL-PRF, IPC Class 3, aerospace):

1. Always select **Density A (Most)** for maximum solder joint strength
2. Enable **"MIL Grade" profile** for:
   - Larger annular rings (minimum 0.05mm extra)
   - Stricter courtyard tolerances
   - Vibration-resistant pad geometries
   - Rounded heel fillets to reduce stress risers
3. Use **Min/Max tolerance stacking** (not RSS) for worst-case analysis
4. Generate PDF report for every footprint → include in design documentation

---

## Contributing

Contributions welcome! Priority areas:
- Additional package families
- Improved IPC formula accuracy
- MIL-STD specific guidelines
- 3D model generation
- KiCad plugin integration

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) (coming soon).

---

## License

**GPL-3.0-or-later** — See [LICENSE](LICENSE).

---

## Status

Early development — Alpha stage. Testers and contributors highly welcome!
