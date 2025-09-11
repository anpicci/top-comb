"""
This script handles the reinterpretation of differential measurements centrally.
"""

# PYTHON LIBRARIES
import os, sys
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
    parser.add_argument(
        '--debug', 
        dest = "debug", 
        action = "store_true",
        default = False,
        help = "Activate debug compiler flags for custom modules"
    )
    return parser.parse_args()

# ----- Code actually starts here ----- # 
if __name__ == "__main__":
    # Load the parsed arguments
    opts = add_parsing_options()
    ROOT.EnableImplicitMT( opts.ncores )


    # Create an instance of the CMGRDF processor

    maker = Processor()

    # Load the configurations
    config_meta = aux.load_config( opts.config )
    operators = aux.get_operators( config_meta['operators'] )
    defs = importlib.import_module( config_meta['definitions'] )

    for analysis_name, analysis_meta in config_meta['analyses'].items():
        
        metadata = aux.load_config( analysis_meta['config'] )
        
        # Load functions 
        for funcfile in metadata['plugins']:
        
            # Control debugging (Todo: check if cmgrdf has its own debug features")
            if opts.debug:
                ROOT.gSystem.AddIncludePath("-D_DEBUGCOMB")
                flag = "g"
                libName = funcfile.replace(".", "_") + ".dbg.so"
                ROOT.EnableImplicitMT( 1 ) # It does not make much sense to debug in multicore
            else:
                flag = "O"
                libName = funcfile.replace(".", "_") + ".so"
        
            ROOT.gSystem.CompileMacro( funcfile, flag )
        
        
        # Load all samples
        samples = cmgdataset.get_cmgrdf_processes( metadata, operators, config_meta['operators']['algo']  )
        
        # Now create the flow
        flow = Flow(
                analysis_name, 
                defs.sequence
        )

        if analysis_meta['sel-plots'] != []:
            plots = [ defs.plots[plot] for plot in analysis_meta['sel-plots'] ]
        else:
            plots = [ defs.plots[plot] for plot in defs.plots.keys() ]
        
        # Book the plotter to generate histograms
        maker.book(
            samples,
            { "all" : 138.0 },
            flow,
            plots,
            eras = [ "all" ],
            withUncertainties = False
        )
        
    results=maker.runPlots()
        
    outpath = os.path.join( os.environ['TOPCOMB_OUTPATH'], config_meta['analysis_name'] )
    
    PlotSetPrinter(
        topRightText="%(lumi).1f fb^{-1} (13.0 TeV)",
        showErrors = False
    ).printSet(
        results, 
        outpath + "/{flow}",
        maxRatioRange=(0.5, 1.5),
        showRatio=True
    )
    
    # Now remake the plots
    #os.system( f"python3 plotter-tools/remake_plots_cmgrdf.py --config {opts.config}" )  
    #os.system( "find %s -type d -exec cp -n templates/index.php {} \;"%outpath )  
