# Generation instructions

This document explains how to use the generation-related modes of the top-comb driver:
`setup_gen`, `run_gridpack` and `run_nanogen`.

## Overview

- `setup_gen` prepares per-analysis generation configuration (MadGraph cards, templates, metadata).
- `run_gridpack` runs the gridpack creation step (MadGraph / gridpack toolchain, packaging, optionally submitting condor jobs).
- `run_nanogen` runs the lightweight "NanoGEN" generation step (CREATES nanoAOD-like output using the prepared gridpacks / samples).

The driver (`top-comb.py`) runs the selected mode for every analysis listed in the main configuration under the `setup` key.

## Prerequisites

- Python 3 (project's environment).
- tmg-tools / NanoGEN runtime for `run_nanogen` if required by your setup.
- Correct `settings.py` (TopCombSettings) for `topcomb_workdir` and other paths.

## Configuration

- Default CLI config file: `main.yml` (or pass a different file with `--config`).

Work directory layout (created under the configured `topcomb_workdir`):
- <workdir_root>/<tag>/generation/<analysis>/...

- The `tag` is chosen with `--tag` and can be created with `--new`.

## Commands / Examples

Create gridpacks (uses prepared configs under the workdir):
```bash
python3 top-comb.py --config main.yml --tag myrun run_gridpack
```

Run NanoGEN generation:
```bash
python3 top-comb.py --config main.yml --tag myrun run_nanogen
```

## Notes
