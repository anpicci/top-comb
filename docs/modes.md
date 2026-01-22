# Modes — Overview

This document describes the control flow and responsibilities without going into implementation details.

## Purpose
Each mode bundles one or more steps that can be executed either once for the whole run or once per analysis defined in the main configuration.

## Key concepts

- Mode builder
  - A small factory function that accepts (workdir, args) and returns a pair: (callable, inputs_dict).
  - Builders perform lazy imports so heavy dependencies are only loaded when a mode runs.

- Callable + inputs
  - The callable is the actual worker function that performs the action.
  - inputs_dict contains keyword arguments passed to the callable when invoked.

- MODE_REGISTRY
  - A mapping of mode name → metadata:
    - "funcs": ordered list of builders (each produces a callable + inputs)
    - "per-analysis": boolean flag indicating whether the resulting callables should be invoked once per analysis entry or once globally

- Driver integration
  - The main driver loads the desired mode(s) from MODE_REGISTRY, invokes each builder to obtain (func, inputs), and then runs the function(s).
  - If "per-analysis" is True, the driver will call the function once for each analysis entry in the main configuration; otherwise the function runs once for the whole tag/workdir.
  - Workdir paths for each mode are derived from the top-level tag workdir (e.g. `<tag>/generation`, `<tag>/analysis`).

## Implemented modes

- setup
  - Prepares per-analysis generation configuration (cards, templates, metadata).

- run_gridpack
  - Creates gridpacks and optionally submits gridpack related jobs.

- run_nanogen
  - Runs the NanoGEN generation step using prepared gridpacks/samples.

- reinterpret
  - Runs the reinterpretation workflow (analysis-level processing and plotting).

## Where to look in the code

- Mode definitions and registry: `modes.py`
- Driver loop and orchestration: `top-comb.py`
- Per-mode implementations: `gen_tools/`, `reinterpret_tools/`
- CLI and settings: `utils/parser.py`, `settings.py`

Keep changes to mode behavior localized: update or add a builder in `modes.py` and implement the worker in the appropriate submodule.