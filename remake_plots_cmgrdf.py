"""
This script replots the shapes produced with CMGRDF.

It assumes the directory structure used in the ttH-MuMu analysis, where 
the output of a given run is organized as follows:

  __OUTPUT_PATH__/__FLOW_NAME__/__ERA__
"""

import os, sys, re
import argparse
import importlib
import glob
from copy import deepcopy
import ROOT as r

import utils.auxiliars as aux
import utils.canvas_utils as cv

# Create the logger instance
from utils.logger import get_logger
from utils.histogram_readers import PlotFileHistogramReader, PlotFileGraphReader
from utils import cmgrdf_datasets as cmgdataset

# Load
from CMGRDF.cms.eras import run3eras

logger = get_logger( __name__ )

# Fix some root stuff
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetPadTickX(1)
r.gStyle.SetPadTickY(1)

# Declare spams for the canvas
spams = [
    { "text" : "__LUMI__ (13.6 TeV)", "x0" : .73, "y0" : .963, "x1" : .755, "y1" : .99, "textsize" : 22 },
    # With preliminary
    #"cmsprel"  : { "text" : r"#splitline{#scale[1.2]{#bf{CMS}}}{#scale[1.0]{#it{Preliminary}}}", #"x0"   : .2, #"y0"   : .825, #"x1"   : .35, #"y1"   : .865, #"textsize" : 22 # Without preliminary
    { "text" : r"#splitline{#scale[1.2]{#bf{CMS}}}{}", "x0" : .2, "y0" : .870, "x1" : .35, "y1" : .885, "textsize" : 22 },
    { "text" : r"__REGION_LABEL__",                    "x0" : .2, "y0" : .83,  "x1" : .35, "y1" : .81,  "textsize" : 22 },
    { "text" : r"__SUBREGION_LABEL__",                 "x0" : .2, "y0" : .75,  "x1" : .35, "y1" : .77,  "textsize" : 22 }
]

def add_parsing_options():
    """ This is a custom parser that allows for passing options to the code """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config', 
        dest = "config", 
        default = "configs/TTG_TOP-23-002.yml", 
        help = "Analysis configuration file."
    )
    return parser.parse_args()


def get_ratio( num, den ):
    """ Computes the ratio between two histograms """
    # Make hard copies
    num = num.Clone( num.GetName() + "_ratio" )
    den = den.Clone( den.GetName() + "_ratio" )
    num.SetDirectory(0)
    den.SetDirectory(0)
    
    for ibin in range( 1, 1 + den.GetNbinsX() ):
        den.SetBinError( ibin, 0 )

    num.Divide( den )
    return num

if __name__ == "__main__":
    opts = add_parsing_options()

    config_meta = aux.load_config( opts.config )
    analysis_name = config_meta['analysis_name']
    lumi_dict = cmgdataset.get_lumi_dict( config_meta['analysis']['samples'] )

    # Get campaign metadata
    analysis_meta = config_meta['analysis']
    flows = analysis_meta['flows']
    plotting = analysis_meta['plotting'] 

    # Load the plot definitions
    plots_module = importlib.import_module( 
        plotting['file'] 
    )
    sel_plots = plots_module.plots
    
    histogram_readers = {}
    # 1. Prepare histogram readers
    grouping_plots = aux.load_config( plotting['groupings'] )
    for entry in grouping_plots[ plotting['splitting'] ]:
        entry_name = entry['name']
        entry_label = entry['label']
        entry_procs = entry['procs']
        entry_stack = entry['stack']
        entry_decorations = entry['histo-decorations']

        reader = PlotFileHistogramReader( 
            entry_name, 
            entry_label,
            entry_procs,
            entry_decorations,
            entry_stack 
        )

        # Add the reader into the list
        histogram_readers[entry_name] = reader
    
    # 2. The second step is to fetch the histograms from the input files 
    outpath_from_cmg = plotting['outpath']
    for flow in flows:
        flow_name = flow['name']
        
        for subflowmeta in flow['subflows']:
            subflow_name = subflowmeta['name']
            subflow_label = subflowmeta['label']
            subflow_sublabel = subflowmeta['sublabel']
            inpath = os.path.join( outpath_from_cmg, f"{analysis_name}/{flow_name}/{subflow_name}" )
            logger.info( f"Remaking plots for flow {inpath}" )
        
            logger.debug( f"Looking for plots in {inpath}" )
            
            if not os.path.exists( inpath ): 
                logger.warning( f"Directory {inpath} does not exist, so skipping." )
                continue
            
            # Fetch all the root files inside this directory
            rfiles = glob.glob( f"{inpath}/*root" )

            for plotcfg in sel_plots:
                rfile = f"{inpath}/{plotcfg.name}.root"
                logger.debug( f"Redoing plots in {rfile}" )

                # First, get the plot metadata
                plot_name = rfile.split("/")[-1].replace(".root", "")
            
                if not plotcfg:
                    logger.warning( f"Plot {plotcfg.name} is not defined in the plots file. Skipping." )
                    continue

                exclude = []
                for readername, reader in histogram_readers.items():
                    logger.debug( f"Making group {readername}" )
                    reader.load( rfile )
                    if not reader.is_valid():
                        exclude.append( readername )

                for excluded_readername in exclude:
                    histogram_readers.pop( excluded_readername ) 

                # Get the histograms from the readers. Split on MC and data
                to_stack = []
                to_overlay = []
                for procname, reader in histogram_readers.items():
                    if reader.stack:
                        to_stack.append( reader.get_histo( rfile ) )
                    else:
                        to_overlay.append( reader.get_histo( rfile ) )

                all_histos = to_stack + to_overlay
                total = PlotFileHistogramReader.integrate( 
                        "total", 
                        to_stack 
                )
                total.SetFillStyle(3444)
                total.SetFillColor( r.kGray+2 )
                total.SetMarkerStyle(0)
                total.SetMarkerColor(920)
                total.SetLineWidth(0)

                for logy_opt in [True, False]:
                    filename = f"{inpath}/{plotcfg.name}" 
                    filename += "_logy" if logy_opt else ""

                    # ---- Prepare the upper pad: stack + total uncertainty + data
                    # Stack all the MC together (TODO: At some point we need to also be able to do
                    # overlines, for more versatility of plotting).
                    hstack = r.THStack()
                    for mchisto in to_stack:
                        hstack.Add( mchisto ) 

                    den = total.Clone( "{filename}_den_ratio" ) # Pick whatever is first
                    ratio_total = get_ratio( den, den )
                    ratio_histos = []
                    for histo in to_overlay:
                        ratio_histos.append( get_ratio( histo, den ) )
                    
                    # Now start plotting
                    c, p1, p2 = cv.new_1d_canvas( f"canvas_{filename}", plotcfg )
                    leg = cv.get_legend( plotcfg, nentries = len(to_stack + to_overlay) )
                    p1.cd()
                    if logy_opt:
                        p1.SetLogy()

                    upper_axis = cv.get_upper_axis( plotcfg, all_histos )
                    upper_axis.Draw( "hist" )

                    # Add to the legend:
                    for readername, reader in histogram_readers.items():
                        
                        leg.AddEntry( 
                            reader.get_histo( rfile ), 
                            reader.get_label(), 
                            "f" if reader.stack else "l"
                        )  

                    leg.AddEntry( 
                        total, 
                        "Uncertainty", 
                        "f"
                    )

                    hstack.Draw("hist same")
                    total.Draw("e2 same")
                    for overlay_h in to_overlay:
                        overlay_h.Draw("hist same")

                    leg.Draw("same")
                    r.gPad.RedrawAxis()

                    p2.cd()
                    lower_axis = cv.get_lower_axis( plotcfg, all_histos )
                    lower_axis.Draw( "hist" )
                    ratio_total.Draw("e2 same")
                    for rh in ratio_histos:
                        rh.Draw("e2 same")

                    r.gPad.RedrawAxis()
                    p1.cd()
                    use_spams = deepcopy( spams )
                    use_spams.extend( getattr( plotcfg, "spams", {} ) ) # Add custom spams 
                    for metaspam in use_spams:
                        text = metaspam["text"]
                        text = text.replace( "__REGION_LABEL__", subflow_label )
                        text = text.replace( "__SUBREGION_LABEL__", subflow_sublabel )
                        text = text.replace( "__LUMI__", "138.0" )
                        cv.doSpam( text, metaspam["x0"], metaspam["y0"], metaspam["x1"], metaspam["y1"], textSize = metaspam["textsize"])

                    # Draw lines (if any)
                    lines = cv.draw_lines_on_hist( all_histos[0], plotcfg )
                    for line in lines:
                        line.Draw("same")

                    # Now save one histogram in linear axis, and
                    # another one in logarithmic
                    c.SaveAs( f"{filename}.pdf" )
                    c.SaveAs( f"{filename}.png" )

                # Finally, keep a log of the yields
                with open( f"{inpath}/{plotcfg.name}_perBin.txt", "w" ) as outfile:
                    for readername, reader in histogram_readers.items():
                        if readername == "data": continue
                        line = f"{readername:10s}\t"
                        h = reader.get_histo( rfile )
                        for ibin in range(1, 1+h.GetNbinsX()):
                            central = h.GetBinContent(ibin)
                            error = h.GetBinError(ibin)
                            line += f"{central:8.2f} +/- {error:8.2f}\t"
                            outfile.write( line )
                        outfile.write( "\n" )

                    line = f"-----------------------------------------------------------------------------------------------\n"
                    outfile.write( line )
                    line += "\n"
                    outfile.write( line )
