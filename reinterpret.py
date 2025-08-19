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
import utils.auxiliars as aux

# Create the logger instance
from utils.logger import get_logger
logger = get_logger( __name__ )


def add_parsing_options():
    """ This is a custom parser that allows for passing options to the code """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config', 
        dest = "config", 
        default = "configs/TTG_TOP-23-002.yml", 
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
    metadata = aux.load_config( opts.config )

    # Load all samples
    samples = cmgdataset.get_cmgrdf_processes( metadata )

    # Load functions 
    for funcfile in metadata['analysis']['plugins']:
        print(funcfile)
        ROOT.gInterpreter.Declare( open( funcfile ).read() )

    # Now load the definitions
    defs = importlib.import_module( metadata['analysis']['definitions'] )


    # Now create the flow
    flow = Flow(
            metadata['analysis_name'], 
            defs.sequence
    )

    # Book the plotter to generate histograms
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
    ).printSet(results, metadata['analysis']['outpath'],
        maxRatioRange=(0.5, 1.5),
        showRatio=True
    )

