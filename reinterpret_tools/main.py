"""
Driver utilities for running the reinterpretation workflow.

This module provides high-level orchestration:
- reinterpret: prepare workdir, update submodules, run a single analysis
  setup (including plotting).
- reinterpret_one_analysis: run the CMGRDF processing pipeline:
  - load datasets and hooks
  - compile plugins
  - build and book flows
  - execute snapshots and plots, then produce PlotSetPrinter output

Functions assume ROOT is available and configured (batch mode, styles).
"""
import os
import ROOT
from copy import deepcopy

from utils import get_logger, \
    load_config, create_dir

from CMGRDF import Processor
from CMGRDF.plots import PlotSetPrinter

from .cmgrdf_datasets import get_cmgrdf_processes 
from .loaders import update_cmgrdf_submodule, load_module_from_path
from .flows import build_sequence, load_selections, build_subflow
from .plotting_tools import replot

logger = get_logger(__name__)

def reinterpret(
        analysis_name, 
        analysis_meta, 
        just_replot,
        workdir, 
        ncores,
        debug,
        doUnc
    ):

    """
    Top-level entry to prepare and run a reinterpretation.
    """
    create_dir(workdir)
    update_cmgrdf_submodule()
    
    reinterpret_meta = load_config(
        analysis_meta["reinterpretation"]
    )
    analysis_workdir = os.path.join(workdir, analysis_name)
    create_dir(analysis_workdir)

    if just_replot:
        logger.info(f"Replotting only for analysis {analysis_name}")
    else:
        logger.warning(f"Setting analysis {analysis_name}")
        reinterpret_one_analysis(
            analysis_name = analysis_name, 
            metadata = reinterpret_meta,
            ncores = ncores,
            debug = debug,
            doUnc = doUnc
        )

    replot(
        analysis_name = analysis_name, 
        metadata = reinterpret_meta
    )

    logger.info("Analysis setup completed.")


def reinterpret_one_analysis(
        analysis_name, 
        metadata,
        ncores,
        debug,
        doUnc,
    ):
    """
    Execute the CMGRDF-based interpretation for a single analysis.

    This function performs the core work:
    1) Load dataset definitions and hooks and translate them into CMGRDF
       process definitions.
    2) Compile any analysis-specific macros/plugins.
    3) Build booking sequences, selections and per-subflow plot targets.
    4) Book flows into a CMGRDF Processor and run snapshots/plots.
    5) Print resulting plots to disk via PlotSetPrinter.
    """

    ROOT.EnableImplicitMT( ncores )
    reinterpretation_meta = metadata.get("reinterpretation")

    # -----------------------------
    # 1. Load samples
    # -----------------------------
    datasets_cfg = reinterpretation_meta["samples"]["datasets"]
    hooks_path = reinterpretation_meta["samples"]["hooks"]

    datasets = load_config(datasets_cfg)
    hooks_module = load_module_from_path("hooks", hooks_path)
    samples = get_cmgrdf_processes(datasets, hooks_module)

    # -----------------------------
    # 2. Plugins
    # -----------------------------
    for funcfile in reinterpretation_meta["plugins"]:
        flag = "g" if debug else "O"

        # ensure headers included by the plugin are found by the compiler:
        plugin_dir = os.path.abspath(os.path.dirname(funcfile))
        if plugin_dir:
            # add the plugin directory to the compiler include path
            ROOT.gSystem.AddIncludePath(f"-I{plugin_dir}")

        if debug:
            ROOT.gSystem.AddIncludePath("-D_DEBUGCOMB")
            ROOT.EnableImplicitMT(1)

        ROOT.gSystem.CompileMacro(funcfile, f"{flag}f++")

    maker = Processor()

    # -----------------------------
    # 3. Flows
    # -----------------------------
    flowmeta = reinterpretation_meta["flow"]

    baseline_sequence = build_sequence(flowmeta["sequence"])
    selections = load_selections(flowmeta["selection"])

    for subflowmeta in flowmeta["subflows"]:
        flow, flow_targets = build_subflow(
            flowmeta=flowmeta,
            subflowmeta=subflowmeta,
            base_sequence=baseline_sequence,
            selections=selections,
            outpath=outpath,
            analysis_name=analysis_name,
        )

        maker.book(
            processes=samples,
            lumi=138.0,
            flows=flow,
            targets=flow_targets,
            withUncertainties = doUnc,
        )

    # -----------------------------
    # 4. Run
    # -----------------------------
    maker.runSnapshots()
    results = maker.runPlots()

    PlotSetPrinter(
        topRightText="%(lumi).1f fb^{-1} (13.6 TeV)",
        showErrors=False
    ).printSet(
        results,
        f"{outpath}/{analysis_name}" + "/{flow}",
        maxRatioRange=(0.5, 1.5),
        showRatio=True,
    )
