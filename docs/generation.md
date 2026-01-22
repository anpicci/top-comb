# Generation instructions

This document explains how to use the generation-related modes of the top-comb driver: `run_gridpack` and `run_nanogen`.

## Overview
- `run_gridpack` runs the gridpack creation step (MadGraph / gridpack toolchain, packaging, optionally submitting condor jobs).
- `run_nanogen` runs the lightweight "NanoGEN" generation step (CREATES nanoAOD-like output using the prepared gridpacks / samples).

The driver (`top-comb.py`) runs the selected mode for every analysis listed in the main configuration under the `setup` key.

## Prerequisites
- Define the generation aspects for your analysis. Instructions on how to setup the `generation.yml` files can be found in this [document](docs/config_files/generation.md)
- tmg-tools for `run_nanogen` if required by your setup.

## Commands / Examples

Create gridpacks (uses prepared configs under the workdir):
```bash
python3 top-comb.py --config main.yml --tag new_comb_run run_gridpack
```

Run NanoGEN generation:
```bash
python3 top-comb.py --config main.yml --tag new_comb_run run_nanogen
```

## Notes

