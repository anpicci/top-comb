"""
This script allows to replot the shapes produced with CMGRDF.
"""
import os, sys, re
sys.path.append( os.environ["TOPCOMB_MAINPATH"] )
import argparse
import importlib
from glob import glob
from copy import deepcopy
import ROOT as r

import utils.auxiliars as aux
import canvas_utils as cv

# Create the logger instance
from utils.logger import get_logger
logger = get_logger( __name__ )

# Fix some root stuff
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetPadTickX(1)
r.gStyle.SetPadTickY(1)

# Declare spams for the canvas
spams = {
            "lumi" : {
                "text" : "138.0 fb^{-1} (13.0 TeV)", 
                "x0"   : .65, 
                "y0"   : .963, 
                "x1"   : .975, 
                "y1"   : .99, 
                "textsize" : 22
            },
            "cmsprel" : {
                # With preliminary 
                "text" : "#splitline{#scale[1.2]{#bf{CMS}}}{#scale[1.0]{#it{Preliminary}}}",
                "x0"   : .2, 
                "y0"   : .825, 
                "x1"   : .35, 
                "y1"   : .865, 
                "textsize" : 22
                # Without preliminary
                #"text" : "#splitline{#scale[1.2]{#bf{CMS}}}{}",
                #"x0"   : .2, 
                #"y0"   : .870, 
                #"x1"   : .35, 
                #"y1"   : .885, 
                #"textsize" : 22        
            },

            "fit" : {
                "text" : '#scale[1.2]{__ANALYSISLABEL__}', 
                "x0"   : .25, 
                "y0"   : .963, 
                "x1"   : .475, 
                "y1"   : .99, 
                "textsize" : 16 
            }
        }

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


def get_histograms( inputFile ):
    """ Grab histograms from the plot file """
    rfile = r.TFile.Open( inputFile )
    histograms = []
    for key in rfile.GetListOfKeys():
        if "total" in key.GetName() or "stack" in key.GetName() or "canvas" in key.GetName():
            continue
        h = deepcopy(rfile.Get( key.GetName()) )
        histograms.append( h )
        
    return histograms

def decorate_histogram( histogram, color ):
    """ Format histograms """

    if color in [0, 10, 18, 19]: # These are white colors that can't be reaed in a plot
        color += 1

    histogram.SetLineColor( color )
    histogram.SetLineWidth( 2 )
    histogram.SetFillColor( 0 )
    return histogram, color + 1


def get_cool_name( name ):
    # Matches things like: ctGminus1p0, ctW0p0, ctX12p34, etc.
    pattern = re.compile(r"c([A-Za-z]+)(minus)?(\d+)p(\d+)")
    
    results = []
    for match in pattern.finditer( name ):
        subindex, minus, int_part, frac_part = match.groups()
        
        # Build the numeric value
        num_str = f"{'-' if minus else ''}{int_part}.{frac_part}"
        num = float(num_str)
        
        # Skip if exactly zero
        if num == 0.0:
            continue
        
        if "minus" in subindex:
            subindex = subindex.replace("minus", "")
            num = f"-{num}"
        results.append(f"C_{{{subindex}}} = {num}")
    
    return ", ".join(results)

def get_ratio( num, den ):
    """ Computes the ratio between two histograms """

    # Make hard copies
    num = deepcopy( num.Clone( num.GetName() + "_ratio" ) )
    den = deepcopy( den.Clone( den.GetName() + "_ratio" ) )

    for ibin in range( 1, 1 + den.GetNbinsX() ):
        den.SetBinError( ibin, 0 )

    num.Divide( den )
    num.SetLineColor( histogram.GetLineColor() )
    num.SetFillColor( 0 )
    num.SetLineWidth( 2 )
    num.SetMarkerSize( 0 )
    return num
    


if __name__ == "__main__":
    opts = add_parsing_options()

    metadata = aux.load_config( opts.config )
    logger.info( f"Remaking plots for analysis: {metadata['analysis_name']}" )
    
    # First grab the plot metadata from the CMGRDF dictionary.
    # This allows us to reuse basic configs such as titles and these
    # kinds of things
    defs = importlib.import_module( metadata['analysis']['definitions'] )

    path_to_plots = metadata['analysis']['outpath']
    logger.debug( f"Remaking plots from: {path_to_plots}" )

    for plot in defs.plots:
        logger.info( f"Doing plot: {plot.name}" )

        # For this plot, grab the shapes from the output path
        plotfile = f"{path_to_plots}/{plot.name}.root"

        # Get the histograms
        histograms = get_histograms( plotfile )
        upper_axis = cv.get_upper_axis( plot, histograms )
        lower_axis = cv.get_lower_axis( plot, histograms )

        # Now create the canvas
        c, p1, p2 = cv.new_1d_canvas( f"canvas_{plot.name}" )
        
        # Get the legend
        leg = cv.get_legend( plot, histograms )
       
        # Prepare the upper pad
        p1.cd()
        upper_axis.Draw("hist")
        color = 1 # Always draw the nominal (SM) in black.
                  # The histograms are sorted that way.
        for ih, histogram in enumerate(histograms):
            histogram, color = decorate_histogram( histogram, color )
            histogram.Draw("hist same")
            cool_name = get_cool_name( histogram.GetName() )
            leg.AddEntry( histogram, cool_name, "l" )
        leg.Draw("same")

        # Now prepare the lower pad
        p2.cd()
        lower_axis.Draw("hist")

        # Now compute the ratios
        ratios = [] # Otherwise ROOT deletes them... 
        for ih, histogram in enumerate(histograms): 
            ratio_hist = get_ratio( num = histogram, den = histograms[0] )
            ratio_hist.Draw("hist same")

            ratios.append( ratio_hist )


        # Finally, decorate the canvas with some spam
        p1.cd()
        for spam, metaspam in spams.items():
            text = metaspam["text"]
            text = text.replace( "__ANALYSISLABEL__", metadata['analysis_name'] )
            cv.doSpam( text, metaspam["x0"], metaspam["y0"], metaspam["x1"], metaspam["y1"], textSize = metaspam["textsize"])

        c.SaveAs( f"{path_to_plots}/{plot.name}_reworked.png" )
        c.SaveAs( f"{path_to_plots}/{plot.name}_reworked.pdf" )

