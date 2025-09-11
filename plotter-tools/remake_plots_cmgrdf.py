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

def get_histograms_from_card( files, procs ):
    """ Grab histograms from the plot file. In this case, we want to plot all the bins for the signal """
    rfile = r.TFile.Open( inputFile )
    histograms = []

    
    nbins = len( procs )

    # Fetch the first one as reference
    f = r.Tfile.Open( files[0] )
    h0 = deepcopy( f.Get( procs[0] ) )

    print( h0 )

    sys.exit()
    for key in rfile.GetListOfKeys():
        if "total" in key.GetName() or "stack" in key.GetName() or "canvas" in key.GetName():
            continue

        index = key.GetName().split("_")[0]
        try: 
            float(index)
            if float(index) not in plot_only: 
                continue
        except:
            pass

        h = deepcopy(rfile.Get( key.GetName()) )
        
        if "SM" in key.GetName():
            histograms.insert( 0, h )
        else:
            histograms.append( h )

        # Normalize histograms
        if norm == "integral":
            histograms[-1].Scale( 1 / histograms[-1].Integral() ) 

    return histograms

def get_histograms( inputFile, plot_only, norm ):
    """ Grab histograms from the plot file """
    rfile = r.TFile.Open( inputFile )
    histograms = []
    for key in rfile.GetListOfKeys():
        if "total" in key.GetName() or "stack" in key.GetName() or "canvas" in key.GetName():
            continue

        index = key.GetName().split("_")[0]
        try: 
            float(index)
            if float(index) not in plot_only: 
                continue
        except:
            pass

        h = deepcopy(rfile.Get( key.GetName()) )
        
        if "SM" in key.GetName():
            histograms.insert( 0, h )
        else:
            histograms.append( h )

        # Normalize histograms
        if norm == "integral":
            histograms[-1].Scale( 1 / histograms[-1].Integral() ) 

    return histograms

def decorate_histogram( histogram, color ):
    """ Format histograms """

    if color in [0, 10, 18, 19]: # These are white colors that can't be reaed in a plot
        color += 1

    histogram.SetLineColor( color )
    histogram.SetLineWidth( 2 )
    histogram.SetFillColor( 0 )
    return histogram, color + 1


def get_cool_name( name, metadata ):

    if not metadata["isEFT"]:
        return metadata["label"]
    if "SM" in name:
        return "SM"
    else:
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

    config_meta = aux.load_config( opts.config )

    operators = aux.get_operators( config_meta['operators'] )

    for analysis_name, analysis_meta in config_meta['analyses'].items():
        logger.info( f"Remaking plots for analysis: {analysis_name}" )
        
        metadata = aux.load_config( analysis_meta['config'] )
        # First grab the plot metadata from the CMGRDF dictionary.
        # This allows us to reuse basic configs such as titles and these
        # kinds of things
        defs = importlib.import_module( metadata['definitions'] )

        path_to_plots = os.path.join( os.environ['TOPCOMB_OUTPATH'], config_meta['analysis_name'], analysis_name )
        logger.debug( f"Remaking plots from: {path_to_plots}" )


        if analysis_meta['sel-plots'] != []:
            plots = [ defs.plots[plot] for plot in analysis_meta['sel-plots'] ]
        else:
            plots = [ defs.plots[plot] for plot in defs.plots.keys() ]

        for plot in plots:
            logger.info( f"Doing plot: {plot.name}" )

            # For this plot, grab the shapes from the output path
            plotfile = f"{path_to_plots}/{plot.name}.root"

            # Get the histograms
            draw_opts = "hist"

            # Fetch the histograms
            histograms = get_histograms_from_card( metadata['files'], metadata['procs'] )

            upper_axis = cv.get_upper_axis( plot, histograms, analysis_meta['norm'] )
            lower_axis = cv.get_lower_axis( plot, histograms, analysis_meta['norm'] )
            
            c, p1, p2 = cv.new_1d_canvas( f"canvas_{plot.name}", plot )
            
            if getattr(plot, "logy", False):
                p1.SetLogy()
                upper_axis.SetMaximum( upper_axis.GetMaximum() * 10 )
                upper_axis.SetMinimum( 1 )

            # Get the legend
            leg = cv.get_legend( plot, histograms )
           
            # Prepare the upper pad
            p1.cd()
            upper_axis.Draw( draw_opts )
            color = 1 # Always draw the nominal (SM) in black.
                      # The histograms are sorted that way.

            if analysis_meta['draw'] == "stack":
                # Draw histograms stacked on top of each other
                color += 1 # Let's avoid a black solid histogram lol
                stack = r.THStack()
                for ih, histogram in enumerate(histograms):
                    histogram, color = decorate_histogram( histogram, color )
                    histogram.SetLineWidth( 1 )
                    histogram.SetFillColor( histogram.GetLineColor() )
                    histogram.SetLineColor( 1 )
                    histogram.SetLineStyle( 1 )
                    stack.Add( histogram )
                    cool_name = get_cool_name( histogram.GetName(), metadata["samples"][histogram.GetName()] )
                    leg.AddEntry( histogram, cool_name, "f" )
                stack.Draw( draw_opts + "same" )
                
            else:
                # Just draw overlined histograms
                for ih, histogram in enumerate(histograms):
                    histogram, color = decorate_histogram( histogram, color )
                    histogram.Draw( f"{draw_opts} same" )
                    cool_name = get_cool_name( histogram.GetName(), metadata["samples"][histogram.GetName()] )
                    leg.AddEntry( histogram, cool_name, "l" )
            leg.Draw("same")

            r.gPad.RedrawAxis()
            # Now prepare the lower pad
            p2.cd()
            lower_axis.Draw( draw_opts )

            # Now compute the ratios
            ratios = [] # Otherwise ROOT deletes them... 
            for ih, histogram in enumerate(histograms): 
                ratio_hist = get_ratio( num = histogram, den = histograms[0] )
                ratio_hist.Draw( f"{draw_opts} same" )
                ratios.append( ratio_hist )


            # Finally, decorate the canvas with some spam
            p1.cd()
            use_spams = deepcopy( spams )
            use_spams.update( getattr( plot, "custom_spams", {} ) ) # Add custom spams 
            for spam, metaspam in use_spams.items():
                text = metaspam["text"]
                text = text.replace( "__ANALYSISLABEL__", config_meta['analysis_name'] )
                cv.doSpam( text, metaspam["x0"], metaspam["y0"], metaspam["x1"], metaspam["y1"], textSize = metaspam["textsize"])


            os.makedirs( f"{path_to_plots}/", exist_ok = True )
            os.system(f"cp templates/index.php {path_to_plots}")
            c.SaveAs( f"{path_to_plots}/{plot.name}.png" )
            c.SaveAs( f"{path_to_plots}/{plot.name}.pdf" )
