# === Standard Library Imports ===
import os
import sys
import tarfile
import argparse
import subprocess
import glob
import importlib
import yaml
from datetime import datetime
from copy import deepcopy
import ROOT

# === Project-Specific Imports ===
from settings import TopCombSettings
from utils import cmgrdf_datasets as cmgdataset
import utils.auxiliars as aux
from utils.logger import get_logger
from utils.GenConfigWriter import GenConfigWriter
from CMGRDF import Processor, Flow, AddWeight
from CMGRDF.plots import Plot, PlotSetPrinter

# === Logger Setup ===
logger = get_logger(__name__)
settings = TopCombSettings().model_dump()

def create_main_parser():
    """Create and return the main argument parser."""
    parser = argparse.ArgumentParser(description="Main parser for the top-comb.py script.")

    parser.add_argument("--config", default="main.yml", type=str, help="Path to config file")
    parser.add_argument("--tag", default="latest", type=str, help="Workdir tag folder to use")
    parser.add_argument("--new", action="store_true", help="Create a new tag")

    subparsers = parser.add_subparsers(dest="mode", required=True)
    add_subcommands(subparsers)
    return parser, subparsers


def add_subcommands(subparsers):
    """Register subcommands for setup modes."""
    setup_gen_parser = subparsers.add_parser("setup_gen", help="Prepare code for generating gridpacks and nanogen inputs.")
    setup_analysis_parser = subparsers.add_parser("setup_analysis", help="Prepare code for shape-based analysis.")

    # Add options for reinterpretation
    reinterpret_parser = subparsers.add_parser("reinterpret", help="Run the reinterpretation of differential measurements.")
    reinterpret_parser.add_argument( '--analysis', dest = "analysis",  default = "TTG_TOP-23-002",  help = "Analysis configuration file." )
    reinterpret_parser.add_argument( '--flow',   dest = "flow",  default = "validation",  help = "Kind of flow one wants to run." )
    reinterpret_parser.add_argument( '--ncores', dest = "ncores",  default = 12, type = int, help = "Number of cores to run with." )
    reinterpret_parser.add_argument( '--doUnc',  dest = "doUnc",  default = True, action = "store_true", help = "Turn on systematic variations." )
    reinterpret_parser.add_argument( '--debug',  dest = "debug",  action = "store_true", default = False, help = "Activate debug compiler flags for custom modules" )


def setup_gen_workdir(workdir, settings, analyses):
    """Set up generation environment with necessary configurations."""
    aux.create_dir(workdir)

    for analysis in analyses:
        metadata = aux.load_config(analysis)
        analysis_name = metadata["analysis_name"]
        logger.warning(f"Setting analysis {analysis_name} ({analysis})")

        samples = metadata["generation"]["samples"]
        operators_meta = metadata["generation"]["operators"]

        gcw = GenConfigWriter(analysis_name)
        for sample in samples:
            proc_metadata = aux.load_config(sample)
            procname = proc_metadata["procname"]
            outdir = os.path.join(workdir, procname)
            aux.create_dir(outdir)
            gcw.setup(settings, proc_metadata, operators_meta, outdir)

            # Compress configuration files
            with tarfile.open(os.path.join(outdir, "cards.tgz"), "w") as tar:
                tar.add(os.path.join(outdir, "mgcards"), arcname="mgcards")

    logger.info("Generation setup completed.")


def setup_analysis(workdir, settings, analyses):
    """Set up the framework for shape-based analysis."""
    aux.create_dir(workdir)
    update_cmgrdf_submodule()

    # Prepare utilities directory
    utilsdir = os.path.join(workdir, "utils")
    aux.create_dir(utilsdir)

    for analysis in analyses:
        metadata = aux.load_config(analysis)
        analysis_name = metadata["analysis_name"]
        analysis_workdir = os.path.join(workdir, analysis_name)

        aux.create_dir(analysis_workdir)
        logger.warning(f"Setting analysis {analysis_name} ({analysis})")

        copy_analysis_files(analysis_workdir, settings, metadata)

    logger.info("Analysis setup completed.")


def update_cmgrdf_submodule():
    """Initialize and update cmgrdf submodule."""
    try:
        subprocess.run(["git", "submodule", "update", "--init", "cmgrdf-prototype"], check=True)
        logger.info("Successfully updated cmgrdf submodule.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error while updating cmgrdf: {e}")


def copy_analysis_files(analysis_dir, settings, metadata):
    """Copy all analysis-specific configuration and plugin files."""
    reinterpretation = metadata["reinterpretation"]
    basepath = settings["topcomb_mainpath"]

    # Copy required configuration files
    files = [
        reinterpretation["datasets"],
        reinterpretation["hooks"],
        reinterpretation["definitions"],
        reinterpretation["sequence"],
        reinterpretation["flows"],
    ]
    for f in files:
        aux.copy_file(os.path.join(basepath, f), dest_dir = analysis_dir)

    # Copy plugin files
    for plugin in reinterpretation.get("plugins", []):
        aux.copy_file(os.path.join(basepath, plugin), dest_dir = analysis_dir)


def determine_tag(tag, new, settings):
    """Determine which tag to use or create."""
    all_tags = os.listdir(settings["topcomb_workdir"])

    if new:
        logger.warning(f"Creating new release: {settings['topcomb_today_tag']}")
        return settings["topcomb_today_tag"]

    if tag not in all_tags + ["latest"]:
        logger.error(f"Tag {tag} does not exist.")
        sys.exit(1)

    latest_tag = max(all_tags)
    if tag == "latest":
        logger.warning(f"Using latest tag: {latest_tag}")
        return latest_tag
    elif tag != latest_tag:
        logger.warning(f"Using a non-latest tag ({tag}). Proceed with caution!")

    return tag

def load_module_from_path(name, path):
    """Dynamically load a Python module from an absolute path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reinterpret(workdir, settings, opts):
    """Launch the reinterpretation code with CMGRDF."""
    ROOT.EnableImplicitMT(opts.ncores)

    analysis_dir =f"{workdir}/{opts.analysis}" 

    # 1. Load the samples
    datasets = aux.load_config( f"{analysis_dir}/datasets.yml" )

    # Load hooks module cleanly (no sys.path hack)
    hooks_module = load_module_from_path("hooks", f"{analysis_dir}/hooks.py")
    samples = cmgdataset.get_cmgrdf_processes(datasets, hooks_module)

    # 2. Load plugins
    for funcfile in glob.glob( f"{analysis_dir}/*.cc"):
        if opts.debug:
            ROOT.gSystem.AddIncludePath("-D_DEBUGCOMB")
            flag = "g"
            libName = funcfile.replace(".", "_") + ".dbg.so"
            ROOT.EnableImplicitMT(1)
        else:
            flag = "O"
            libName = funcfile.replace(".", "_") + ".so"

        ROOT.gSystem.CompileMacro(funcfile, flag)

    # 3. Create the processor instance
    maker = Processor()

    # 4. Book all the flows
    flows_meta = aux.load_config( f"{analysis_dir}/flows.yml")
    sequence_meta = aux.load_config( f"{analysis_dir}/sequence.yml")
    subflows = flows_meta[opts.flow]

    definitions_module = load_module_from_path("definitions", f"{analysis_dir}/definitions.py")
    plots_module = load_module_from_path("plots", f"{analysis_dir}/plots.py")

    for subflow in subflows:
        logger.info(f"Booking subflow: {subflow}")

        # Prepare the sequence
        sequence = []
        for step in sequence_meta[subflow["sequence"]]:
            objtype = step["name"]
            func_name = step["function"]
            args = step["args"]

            func = getattr(definitions_module, func_name)
            logger.info(f"Defining obj: {objtype}")
            logger.debug(f"definitions function: {func_name}")
            logger.debug(f"arguments: {args}")

            sequence.extend(func(args))

        flow = Flow(f"{opts.analysis}/{subflow['name']}", sequence)
        targets = plots_module.plots

        maker.book(
            processes=samples,
            lumi=138.0,
            flows=flow,
            targets=targets,
            withUncertainties=opts.doUnc,
        )

    # 5. Make plots
    results = maker.runPlots()
    PlotSetPrinter(
        topRightText="%(lumi).1f fb^{-1} (13.6 TeV)",
        showErrors=False,
    ).printSet(
        results,
        f"{opts.analysis}/{opts.flow}/",
        maxRatioRange=(0.5, 1.5),
        showRatio=True,
    )

def main():
    parser, _ = create_main_parser()
    args = parser.parse_args()

    main_config = aux.load_config( args.config )
    tag = determine_tag(args.tag, args.new, settings)
    mode = args.mode

    workdir = os.path.join(settings["topcomb_workdir"], tag)
    logger.info(f"Running mode: {mode}")

    if mode == "setup_gen":
        
        setup_gen_workdir( 
            workdir = os.path.join(workdir, "generation"), 
            settings = settings, 
            analyses = main_config["setup"] 
        )

    elif mode == "setup_analysis":
        
        setup_analysis( 
            workdir = os.path.join(workdir, "analysis"), 
            settings = settings, 
            analyses = main_config["setup"] 
        )

    elif mode == "reinterpret":
        
        reinterpret( 
            workdir = os.path.join(workdir, "analysis"),
            settings = settings,
            opts = args 
        )

    else:
        logger.error(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
