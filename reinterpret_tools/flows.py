"""
flows
-----

Helpers to build booking sequences and per-subflow configurations used by the
CMGRDF Processor booking API.

Responsibilities:
- build_sequence(seq_meta): convert a high-level sequence description into
  a runnable booking/processing sequence used by CMGRDF flows.
- load_selections(selection_cfg): load selection definitions referenced by
  subflows and sequences.
- build_subflow(flowmeta, subflowmeta, base_sequence, selections, outpath,
  measurement_name): construct a flow and its plot/target descriptors for a
  particular sub-measurement (subflow).

Each public function documents the shape of the expected input metadata and
returns objects compatible with the booking procedure in reinterpret_driver.
"""

import sys
import ROOT
from copy import deepcopy
from utils.logger import get_logger
from CMGRDF import Flow, Cut, Define
from .loaders import load_module_from_path


logger = get_logger(__name__)
def build_sequence(steps):
    """Build sequence of definitions from YAML metadata."""
    seq = []
    for meta in steps:
        module = load_module_from_path(
            f"definitions_{meta['modules']}",
            meta["modules"]
        )
        func = getattr(module, meta["function"])
        args = meta.get("args", {})
        name = meta.get("name", meta["function"])

        logger.info(f"Defining object: {name}")
        logger.debug(f"Module={meta['modules']} Function={meta['function']} Args={args}")

        seq.extend(func(args))
    return seq


def build_cuts(cut_definitions):
    """Convert YAML cut definitions into Cut objects."""
    out = []
    for c in cut_definitions:
        expr = c["expr"]
        if isinstance(expr, list):
            expr = " && ".join(expr)
        out.append(Cut(c["name"], expr))
    return out


def load_selections(meta):
    """Load baseline + channel-specific selections."""
    cuts = {"base": build_cuts(meta.get("baseline", []))}
    for channel, defs in meta.get("channels", {}).items():
        cuts[channel] = build_cuts(defs)
    return cuts


def build_subflow(flowmeta, subflowmeta, base_sequence, selections, outpath, measurement_name):
    """Construct a Flow and its targets."""
    flowname = flowmeta["name"]
    subname = subflowmeta["name"]
    channel = subflowmeta["channel"]
    weights = subflowmeta.get("weights", [])

    fullname = f"{flowname}_{subname}"
    logger.info(f"Building subflow: {fullname}")

    seq = deepcopy(base_sequence)
    seq.extend(selections["base"])
    seq.extend(selections[channel])

    # ---- Targets ----
    plot_targets = []
    snap_targets = []

    for tmeta in flowmeta["targets"]:
        if tmeta["type"] != "plots":
            logger.error(f"Target type '{tmeta['type']}' not implemented.")
            sys.exit(1)

        plots_module = load_module_from_path("plots", tmeta["plotfile"])
        plotmods = tmeta["plotmodule"]

        if isinstance(plotmods, list):
            for pm in plotmods:
                plot_targets.extend(getattr(plots_module, pm))
        else:
            plot_targets.extend(getattr(plots_module, plotmods))

        if tmeta["save_snapshot"]:
            columnSel = []
            for p in plot_targets:
                name = p.getOpt("name")
                expr = p.getOpt("_expr")
                seq.append(Define(name, expr))
                columnSel.append(name)

            snap_path = (
                f"{outpath}/{measurement_name}/{flowname}/{subname}"
                "/snapshots/{name}.root"
            )

            from CMGRDF import Snapshot
            snap_targets.append(
                Snapshot(
                    snap_path,
                    columnSel=["weight"] + columnSel,
                    compression=None,
                )
            )

    if not weights:
        logger.warning(f"{fullname}: running without weight corrections!")

    flow = Flow(f"{flowname}/{subname}", seq)
    return flow, (plot_targets + snap_targets)
