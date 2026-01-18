"""
Driver utilities for running the reinterpretation workflow.

This module provides high-level orchestration:
- reinterpret: prepare workdir, update submodules, run a single measurement
  setup (including plotting).
- reinterpret_one_measurement: run the CMGRDF processing pipeline:
  - load datasets and hooks
  - compile plugins
  - build and book flows
  - execute snapshots and plots, then produce PlotSetPrinter output

Functions assume ROOT is available and configured (batch mode, styles).
"""
import os, sys
import ROOT
from utils import (
    get_logger,
    load_module_from_path
)
from environment import TopCombEnv

from CMGRDF import Processor
from CMGRDF.plots import PlotSetPrinter
from CMGRDF import Flow, Cut, Define

from .dataset_utilities import read_datasets 

logger = get_logger(__name__)


def build_sequence(steps, doSyst=False, eras=["all"]):
    """Build sequence of definitions from YAML metadata."""
    sequences = []
    
    for name, file_module in steps.items():
        module_file, module_seq = file_module.split(":")
        module = load_module_from_path(f"definitions_{name}", module_file)
        
        seq = getattr(module, module_seq)
        
        if isinstance(seq, list):
            for func in seq:
                sequences.extend( 
                    func() 
                )
        else:
            sequences.extend(
                seq()
            )
    
    return sequences

def load_selections(meta):
    """Load baseline + channel-specific selections."""
    cuts = []
    for cutflow, filefunc in meta.items():
        file, cutfunc = filefunc.split(":")

        module = load_module_from_path(f"selections_{cutflow}", file)

        cuts += getattr(module, cutfunc)()

    return cuts


def process_flow_config(config, doUnc=False, eras=None):
    """
    Process flow configuration to build sequence and selections.
    
    Args:
        config: Flow configuration dictionary
        base_sequence: Base sequence to extend (if None, starts empty)
        base_selections: Base selections to extend (if None, starts empty)
        doUnc: Whether to include systematic uncertainties
        eras: List of eras to process
    """
    sequence = []
    selections = []
    
    if "sequence" in config:
        steps = build_sequence(
            config["sequence"],
            doSyst=doUnc,
            eras=eras if eras else []
        )
        sequence.extend(steps)
    
    if "selection" in config:
        additional_selections = load_selections(config["selection"])
        selections.extend(additional_selections)
    
    return sequence, selections


def build_targets(config, sequence, flowname, outpath, measurement_name):
    """
    Build plot and snapshot targets from configuration.

    Args:
        config: Configuration dictionary containing targets
        sequence: Current sequence (will be modified if snapshots are saved)
        flowname: Name of the flow
        outpath: Output path for results
        measurement_name: Name of the measurement
    
    """
    plot_targets = []
    snap_targets = []
    
    if "targets" not in config:
        return []
    
    for tmeta in config["targets"]:
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
        
        if tmeta.get("save_snapshot", False):
            columnSel = []
            for p in plot_targets:
                name = p.getOpt("name")
                expr = p.getOpt("_expr")
                sequence.append(Define(name, expr))
                columnSel.append(name)
            
            snap_path = (
                f"{outpath}/{measurement_name}/{flowname}/"
                "/snapshots/{{name}}.root"
            )
            
            from CMGRDF import Snapshot
            snap_targets.append(
                Snapshot(
                    snap_path,
                    columnSel=["weight"] + columnSel,
                    compression=None,
                )
            )
    
    return plot_targets + snap_targets


def build_flow(
        flowname, 
        config,  
        outpath=None, 
        measurement_name=None, 
        doUnc=False, 
        eras=None
    ):
    """
    Construct a Flow and its targets from configuration.
    """
    logger.info(f"Building flow: {flowname}")
    
    # Process configuration to build sequence and selections
    sequence, selections = process_flow_config(
        config,
        doUnc=doUnc,
        eras=eras
    )

    # Build targets
    targets = build_targets(
        config,
        sequence,
        flowname,
        outpath,
        measurement_name
    )
    
    # Create flow
    for step in sequence + selections:
        logger.debug(f"Flow step: {step}")
        
    flow = Flow(f"{flowname}/", sequence + selections)
    
    return flow, targets


def reinterpret_one_measurement(
         measurement_name, 
        outpath,
        metadata,
        lumis,
        ncores,
        debug,
        doUnc,
    ):
    """
    Execute the CMGRDF-based interpretation for a single measurement.

    This function performs the core work:
    1) Load dataset definitions and hooks and translate them into CMGRDF
       process definitions.
    2) Compile any measurement-specific macros/plugins.
    3) Build booking sequences, selections and per-subflow plot targets.
    4) Book flows into a CMGRDF Processor and run snapshots/plots.
    5) Print resulting plots to disk via PlotSetPrinter.
    """

    ROOT.EnableImplicitMT( ncores )

    # -----------------------------
    # 1. Load samples
    # -----------------------------
    hooks_path = metadata["samples"]["hooks"]
    datasets_path = metadata["samples"]["datasets"]

    samples = []

    eras = []
    for dataset_era, dataset_file in datasets_path.items():
        datasets_module = load_module_from_path("datasets", dataset_file)
        hooks_module = load_module_from_path("hooks", hooks_path)
        samples.extend( 
            read_datasets(
                str(dataset_era), 
                datasets_module, 
                hooks_module)
        )
        eras.append( str(dataset_era) )

    # -----------------------------
    # 2. Plugins
    # -----------------------------
    for funcfile in metadata["plugins"]:
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
    baseline_config = metadata["baseline"]
    baseline_name = baseline_config["name"]

    # Build flows for each subflow
    for subflow_config in metadata["subflows"]:
        flowname = subflow_config["name"]
        
        fullname = f"{baseline_name}/{flowname}"
        # Merge baseline and subflow configurations
        flow_config = {**baseline_config, **subflow_config}
        
        flow, targets = build_flow(
            flowname=fullname,
            config=flow_config,
            outpath=outpath,
            measurement_name=measurement_name,
            doUnc=doUnc,
            eras=eras
        )

        maker.book(
            processes=samples,
            lumi=lumis,
            flows=flow,
            targets=targets,
            eras=eras,
            withUncertainties=doUnc,
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
        f"{outpath}/{measurement_name}" + "/{flow}",
        maxRatioRange=(0.5, 1.5),
        showRatio=True,
    )