import ROOT
ROOT.gROOT.SetBatch(1)
ROOT.gStyle.SetOptStat(0)
ROOT.ROOT.EnableImplicitMT( 12 )
ROOT.gStyle.SetPaintTextFormat(".1f")
ROOT.gStyle.SetPalette( ROOT.kViridis )
ROOT.gStyle.SetPadTickX(1)
ROOT.gStyle.SetPadTickY(1)

from .plotter1d import Plotter1D



