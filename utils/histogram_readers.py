""" Classes for reading out histograms from either plot or card files """
import os, re, sys
import ROOT as r
from copy import deepcopy
import math
import importlib

from utils.logger import get_logger
logger = get_logger( __name__ )

colors_module = importlib.import_module( 
    'utils.cms_pallete' 
)

class HistogramReader:
    """Abstract base for histogram readers."""
    def __init__(self, name, label, procs, decorations, stack):
        self.name = name
        self.h_nominal = []
        self.cache = {}
        self.label = label
        self.procs = procs
        self.stack = stack
        self.decorations = decorations or {} 
        self.valid = True

    def load( self, inputFile ):
        self.fetch( inputFile )
        if self.is_valid(): # Do not further operate if it is not a valid input
            self.decorate( inputFile )

    def fetch(self, *args, **kwargs):
        """Override this in subclasses to return a list of ROOT histograms."""
        raise NotImplementedError

    def get_histo(self, inputFile):
        return self.cache[inputFile]

    def get_label(self):
        return self.label

    def is_valid(self):
        return ( self.valid )

    def decorate(self, inputFile):
        """ Apply custom decorations to the nominal histogram """ 
        for func, value in self.decorations.items():
            if "Color" in func:
                value = getattr( colors_module, value ) 
            evalfunc = getattr( self.cache[inputFile], func )
            evalfunc( value )

    @staticmethod
    def integrate( name, histograms ):
        """ Reads a dictionary and integrates histograms together """
        h0 = histograms[0].Clone( f"{name}_SUM" )
        h0.SetDirectory(0)
        for h in histograms[1:]:
            h0.Add( h )
        return h0


class PlotFileHistogramReader( HistogramReader ):
    """Reader for histograms """
    def fetch(self, inputFile ):

        if inputFile in self.cache:
            return  # already loaded

        self.cache[inputFile] = None 

        with r.TFile.Open(inputFile) as rfile:
            
            histograms = []

            for proc in self.procs:

                nominal_h = None
                variations = []
                for key in rfile.GetListOfKeys():
                    hname = key.GetName()

                    if any( x in hname for x in ["data", "canvas"] ): continue
                    if not hname.startswith( proc ):
                        continue

                    if proc == hname:
                        nominal_h = rfile.Get( hname ).Clone()
                    else:
                        variations.append( rfile.Get( hname ).Clone() )

                if not nominal_h:
                    logger.warning( f'Process {proc} not in {inputFile}!' )
                    continue
                
                # At this point, add the variations to the nominal histogram
                # Note: the nominal histogram already has the MC stat uncertainties.
                for ibin in range( 1, 1 + nominal_h.GetNbinsX() ):
                    content = nominal_h.GetBinContent( ibin )

                    err = nominal_h.GetBinError(ibin)*nominal_h.GetBinError(ibin)
                    for hvar in variations:
                        content_var = hvar.GetBinContent( ibin )
                        diff = content - content_var
                        err += diff*diff
                    nominal_h.SetBinError( ibin, math.sqrt( err ) )
                        
                # Finally save this histogram in cache
                histograms.append( nominal_h )

            # Now integrate all together and cache it
            if histograms != []:
                self.cache[inputFile] = PlotFileHistogramReader.integrate( 
                        self.name, 
                        histograms 
                ) 
            else:
                logger.warning( f'Group {self.name} could not be created as there are no valid inputs.' )
                self.valid = False
            
            
class PlotFileGraphReader( HistogramReader ):
    """Reader for graphs """
    def fetch(self, inputFile ):
        if inputFile in self.cache:
            return  # already loaded
        self.cache[inputFile] = {}
        with r.TFile.Open(inputFile) as rfile:
            
            grname = 'data_graph' 
            copy_gr = rfile.Get(grname).Clone()
            for ipoint in range( copy_gr.GetN() ):
                copy_gr.SetPointError(ipoint, 0, 0, copy_gr.GetErrorYlow(ipoint), copy_gr.GetErrorYhigh(ipoint) )

            self.cache[inputFile] = copy_gr
