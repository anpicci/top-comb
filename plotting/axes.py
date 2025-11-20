"""
axes

AxisBuilder: general helper to construct a ROOT.TH1-like histogram that can
be used as an axis template for plotting pads.

The class accepts either a single reference object (TH1/THStack/TGraph) or a
list of reference objects and exposes small configuration knobs (logy,
fixed y-range, ratio range, bin labels, titles).
"""
from dataclasses import dataclass
from typing import Any, Optional, Sequence, Tuple, Union
import ROOT
from dataclasses import dataclass
from typing import Optional, Tuple, Sequence

RefObj = Union[
    ROOT.TH1, 
    ROOT.THStack, 
    ROOT.TGraph, 
    Any
]

@dataclass
class AxisParameters:
    title: str = "Title"
    range: Optional[ Tuple[float, float] ] = "__auto__"
    label_font: int = 43
    label_size: int = 24
    label_offset: float = 0.01
    ndivisions: int = 510
    title_font: int = 43
    title_size: int = 24
    title_offset: float = 1.5
    centertitle: bool = False
    xBinLabels: Optional[Sequence[str]] = None


class AxisBuilder:
    ref_objs = []
    paramsX = AxisParameters()
    paramsY = AxisParameters()

    def __init__(
            self, 
            ref_objs, 
            paramsX: AxisParameters = AxisParameters(), 
            paramsY: AxisParameters = AxisParameters() 
        ):
        self.ref_objs = ref_objs
        self.paramsX = paramsX
        self.paramsY = paramsY

    def build(self) -> ROOT.TH1:
        """Build a TH1 usable as axis """
        base = self._choose_base()
        haxis = self._clone_or_dummy(base)
        haxis.SetTitle("")
        self.apply_axis_params(haxis.GetXaxis(), self.paramsX)
        self.apply_axis_params(haxis.GetYaxis(), self.paramsY)

        # Apply explicit X/Y/Z ranges if provided
        if self.paramsY.range != "__auto__":
            lo, hi = self.paramsY.range
            haxis.SetMinimum( float(lo) )
            haxis.SetMaximum( float(hi) )
        else:
            minimum, maximum = self.get_auto_y_range( self.ref_objs )
            haxis.GetYaxis().SetRangeUser( minimum, maximum )

        return haxis
    
    def get_auto_y_range(self, refs):
        # Y-axis scaling
        maximum = 0.0
        minimum = 0.01
        for obj in refs:
            if isinstance(obj, ROOT.TH1):
                maximum = max(maximum, obj.GetMaximum())
            elif isinstance(obj, ROOT.TGraph):
                yvals = [obj.GetY()[i] for i in range(obj.GetN())]
                maximum = max(maximum, max(yvals))
        
        maximum = max(maximum, 1e-3)
        return minimum, maximum * 2.5

    def _choose_base(self):
        """Find a histogram-like base object for binning (TH1) from ref_objs."""
        if not self.ref_objs:
            raise ValueError("No reference objects provided to AxisBuilder.")
        
        first = self.ref_objs[0]
        # If first is THStack, try to use the top-most histogram in the stack
        if isinstance(first, ROOT.THStack):
            stack = first.GetStack()
            if stack and stack.GetSize() > 0:
                base = stack.Last()
                if base: return base
        # fallback: look for the first TH1 among all refs
        for o in self.ref_objs:
            if isinstance(o, ROOT.TH1):
                return o
            # if THStack exists further in list
            if isinstance(o, ROOT.THStack):
                stack = o.GetStack()
                if stack and stack.GetSize() > 0:
                    return stack.Last()
        # last fallback: if a TGraph is provided, create a dummy histo later
        for o in self.ref_objs:
            if isinstance(o, ROOT.TGraph):
                return o
        raise TypeError("No histogram-like object available to define axis.")

    def _clone_or_dummy(self, base):
        """Return a detached clone of a TH1 base or a dummy TH1 for TGraph."""
        if isinstance(base, ROOT.TH1):
            h = base.Clone(base.GetName() + "_axis")
            h.SetDirectory(0)
            return h
        if isinstance(base, ROOT.TGraph):
            # build simple histogram spanning graph Y-range
            n = base.GetN()
            yvals = [base.GetY()[i] for i in range(n)]
            ymin = min(yvals) if yvals else 0.0
            ymax = max(yvals) if yvals else 1.0
            nbins = max(10, int(n))
            h = ROOT.TH1F("axis_dummy", "", nbins, ymin, ymax)
            h.SetDirectory(0)
            return h
        raise TypeError(f"Unsupported base type: {type(base)}")

    def apply_axis_params(self, axis, params):
        # Title
        axis.SetTitle( params.title )

        # Label styling
        axis.SetLabelFont(params.label_font)
        axis.SetLabelSize(params.label_size)

        # Title styling
        axis.SetTitleFont(params.title_font)
        axis.SetTitleSize(params.title_size)
        axis.SetTitleOffset(params.title_offset)

        # Center title if requested
        if getattr(params, "centertitle", False):
            axis.CenterTitle(True)

        # Divisions (only for X/Y when available)
        if hasattr(params, "ndivisions"):
            axis.SetNdivisions(params.ndivisions)



