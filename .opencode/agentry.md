# Agent Configuration

## Commands

- **build**: `pip install -e . && python -c "from kicad_mil_fpgen import *; print('OK')"`
- **test**: `pytest tests/ -v`
- **lint**: `black --check src/ tests/`
- **typecheck**: `mypy src/`

## Repository Overview

This is the KiCad MIL IPC-7351 Footprint Generator — a desktop application that generates IPC-7351C compliant KiCad footprints with MIL-STD / high-reliability presets.

Key directories:
- `src/kicad_mil_fpgen/core/` — Pure math engine (IPC calculations, tolerances)
- `src/kicad_mil_fpgen/gui/` — PySide6 UI
- `src/kicad_mil_fpgen/models/` — Data classes
- `src/kicad_mil_fpgen/export/` — KiCad file generation
- `ipc_data/` — YAML/JSON tables with IPC-7351 formulas
- `templates/` — User profiles and MIL presets

Tech: Python 3.11+, PySide6, NumPy, pandas, reportlab (PDF), matplotlib (preview)
