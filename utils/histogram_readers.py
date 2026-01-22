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
    def __init__(self, name, label, procs, decorations):
        self.name = name
        self.h_nominal = []
        self.cache = {}
        self.label = label
        self.procs = procs
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
        """Return a detached clone of the cached histogram for external use."""
        key = os.path.abspath(inputFile)
        h = self.cache.get(key)
        if h is None:
            return None
        # Always return a clone detached from any file
        clone = h.Clone(f"{h.GetName()}_clone")
        clone.SetDirectory(0)
        return clone

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
    def integrate(name, histograms):
        """Integrate (sum) a list of histograms and return a detached clone.

        Returns None if histograms is empty.
        """
        if not histograms:
            return None
        h0 = histograms[0].Clone(f"{name}_SUM")
        h0.SetDirectory(0)
        for h in histograms[1:]:
            h0.Add(h)
        return h0


class PlotFileHistogramReader( HistogramReader ):
    """Reader for histograms """
    def fetch(self, inputFile ):

        inputFile = os.path.abspath(inputFile)
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
                    if any(x in hname for x in ["data", "canvas"]): continue
                    if not hname.startswith(proc): continue
                    obj = rfile.Get(hname)
                    if obj is None: continue
                    cloned = obj.Clone()
                    cloned.SetDirectory(0)
                    if proc == hname:
                        nominal_h = cloned
                    else:
                        variations.append(cloned)

                if not nominal_h:
                    logger.warning(f'Process {proc} not in {inputFile}!')
                    continue
                # combine variations into nominal errors ...
                for ibin in range(1, 1 + nominal_h.GetNbinsX()):
                    content = nominal_h.GetBinContent(ibin)
                    err = nominal_h.GetBinError(ibin)**2
                    for hvar in variations:
                        diff = content - hvar.GetBinContent(ibin)
                        err += diff * diff
                    nominal_h.SetBinError(ibin, math.sqrt(err))
                histograms.append(nominal_h)

            if histograms:
                self.cache[inputFile] = PlotFileHistogramReader.integrate(self.name, histograms)
            else:
                logger.warning(f'Group {self.name} could not be created as there are no valid inputs.')
                self.valid = False

class PlotFileGraphReader( HistogramReader ):
    """Reader for graphs """
    def fetch(self, inputFile ):
        inputFile = os.path.abspath(inputFile)
        if inputFile in self.cache:
            return
        self.cache[inputFile] = None
        with r.TFile.Open(inputFile) as rfile:
            grname = 'data_graph'
            obj = rfile.Get(grname)
            if obj is None:
                logger.warning(f"Graph {grname} not found in {inputFile}")
                self.valid = False
                return
            copy_gr = obj.Clone()
            # normalize point errors format, keep clone detached
            for ipoint in range(copy_gr.GetN()):
                copy_gr.SetPointError(ipoint, 0, 0, copy_gr.GetErrorYlow(ipoint), copy_gr.GetErrorYhigh(ipoint))
            self.cache[inputFile] = copy_gr
