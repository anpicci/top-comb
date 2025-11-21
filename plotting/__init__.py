# geofit/plotting/__init__.py
from .base_plotter import PlotterBase
from .plotter1d import Plotter1D

__all__ = ["PlotterBase", "PlotConfig", "Plotter1D"]

import ROOT
ROOT.gROOT.SetBatch(1)
ROOT.gStyle.SetOptStat(0)
ROOT.ROOT.EnableImplicitMT( 12 )
ROOT.gStyle.SetPaintTextFormat(".1f")
ROOT.gStyle.SetPalette( ROOT.kViridis )
ROOT.gStyle.SetPadTickX(1)
ROOT.gStyle.SetPadTickY(1)





