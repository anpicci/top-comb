"""
This script handles the reinterpretation of differential measurements centrally.
"""

# PYTHON LIBRARIES
import sys
import argparse
import ROOT 
import yaml
import importlib

# CMGRDF SPECIFIC LIBRARIES
from CMGRDF import Processor, Flow, AddWeight
from CMGRDF.plots import Plot, PlotSetPrinter

# Utilities to be interface with CMGRDF
from utils import cmgrdf_datasets as cmgdataset

def load_config( config_path ) -> dict:
    """ Loads a configuration file written in yml format """
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def add_parsing_options():
    """ This is a custom parser that allows for passing options to the code """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config', 
        dest = "config", 
        default = "inputs/configs/TTG_TOP-23-002.yml", 
        help = "Analysis configuration file."
    )
    parser.add_argument(
        '--ncores', 
        dest = "ncores", 
        default = 12,
        type = int,
        help = "Number of cores to run with."
    )
    return parser.parse_args()

# ----- Code actually starts here ----- # 
if __name__ == "__main__":
    # Load the parsed arguments
    opts = add_parsing_options()
    ROOT.EnableImplicitMT( opts.ncores )

    # Load the configurations
    metadata = load_config( opts.config )

    # Load all samples
    samples = cmgdataset.get_cmgrdf_processes( metadata['analysis']['samples'] )

    # Load functions 
    for funcfile in metadata['analysis']['plugins']:
        ROOT.gInterpreter.Declare( open( funcfile ).read() )

        # Say hello
        ROOT.printHello()

    # Now load the definitions
    defs = importlib.import_module( metadata['analysis']['definitions'] )


    # Now create the flow
    flow = Flow(
            metadata['analysis_name'], 
            defs.sequence
    )

    maker = Processor()

    maker.book(
        samples,
        { "all" : 138.0 },
        flow,
        defs.plots,
        eras = [ "all" ],
        withUncertainties = False
    )

    results=maker.runPlots()

    PlotSetPrinter(
        topRightText="%(lumi).1f fb^{-1} (13.0 TeV)",
        showErrors = False
    ).printSet(results, f"outplots/{metadata['analysis_name']}/",
        maxRatioRange=(0.5, 1.5),
        showRatio=True
    )

    """
    flow_srwz = Flow("srwz", sequence)

    maker = Processor()

    maker.book(
        processes,
        lumi, 
        flow_srwz,
        plots_wz,
        eras = eras,
        withUncertainties = run_unc
    )

    # This creates the plots
    results=maker.runPlots( mergeEras = True )


    # This saves the plots in the `output folder`
    # One can find more about this in `cmgrdf-prototype/python/CMGRDF/plots.py`.
    PlotSetPrinter(
        topRightText="%(lumi).1f fb^{-1} (13.6 TeV)",
        showErrors=run_unc
    ).printSet(results, outfolder + f"/{year}/",
        maxRatioRange=(0.5, 1.5),
        showRatio=True
    )


    """
