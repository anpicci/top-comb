import ROOT
from copy import deepcopy
import numpy as np
from plotting import PlotterBase
from plotting.axes import AxisBuilder, AxisParameters
from plotting.legend import LegendBuilder
from plotting.canvas import CanvasBuilder, CanvasParameters
from utils import get_logger
import sys

logger = get_logger(__name__)

class Plotter1D(PlotterBase):
    """CMS-style 1D plotter for histograms and graphs."""

    config = CanvasParameters.with_ratio()

    # -------------------------------------------------------------------------
    def _draw(self, 
            name, 
            hists = None, 
            ratios = None,
            funcs = None, 
            graphs = None,
            labels = None, 
            plot_customizations = None, 
            spams = None
        ) -> ROOT.TCanvas:
            
        """Draw 1D plots supporting histograms, graphs, and optional functions."""
        ref_objs = hists + graphs
        if ref_objs == []:
            logger.error("No histograms or graphs provided to plotter.")
            sys.exit(1)

        # ------------- Prepare the canvas and the axes ------------- #
        c, pads = CanvasBuilder( self.config ).build( name )

        # ------------- Draw the upper axis ------------- #
        # Upper axis
        upperAxisParamsX = AxisParameters( 
            label_size = 0, 
            title_size = 0 
        )
        upperAxisParamsY = AxisParameters( 
            plot_customizations.yTitle 
        )
        upper_axis = AxisBuilder( 
            ref_objs = ref_objs, 
            paramsX = upperAxisParamsX, 
            paramsY = upperAxisParamsY 
        ).build()
        legend = LegendBuilder().build()
        p1 = pads["main"]
        p1.cd()
        if plot_customizations.logy:
            p1.SetLogy()
        upper_axis.Draw("hist")
        
        self.print_spam( plot_customizations.annotations + spams )
        for obj in zip(ref_objs + funcs, labels):
            if isinstance(obj[0], ROOT.TH1):
                obj[0].Draw("hist same")
                legend.AddEntry(obj[0], obj[1], "lf")
            elif isinstance(obj[0], ROOT.TGraph):
                obj[0].Draw("PE1 same")
                legend.AddEntry(obj[0], obj[1], "p")
            elif isinstance(obj[0], ROOT.TF1):
                obj[0].Draw("same")
                legend.AddEntry(obj[0], obj[1], "l")
        legend.Draw("same")
        p1.RedrawAxis()

        # ------------- Draw the lower axis ------------- #
        # Lower axis
        lowerAxisParamsX = AxisParameters( 
            title = plot_customizations.xTitle, 
            label_size = 22, 
            title_offset = 1.05 
        )
        lowerAxisParamsY = AxisParameters( 
            title = "Data/Pred.", 
            range = plot_customizations.RatioRange, 
            centertitle = True, 
            ndivisions = 503
        )
        lower_axis = AxisBuilder( 
            ref_objs = ref_objs, 
            paramsX = lowerAxisParamsX, 
            paramsY = lowerAxisParamsY 
        ).build()

        p2 = pads["ratio"]
        p2.cd()
        lower_axis.Draw("hist")
        for ratio in ratios:
            ratio.SetMarkerSize(0)
            ratio.Draw("e2 same")

        return deepcopy(c)