from dataclasses import dataclass
import ROOT

@dataclass
class LegendParameters:
    """Holds configurable legend parameters."""
    corner: str = "TR"
    text_size: float = 0.046
    ncolumns: int = 2
    x1: float = 0.38
    y1: float = 0.72
    x2: float = 0.89
    y2: float = 0.905
    font: int = 42

class LegendBuilder:
    """Builds a ROOT.TLegend from LegendParameters."""

    def __init__(self, params: LegendParameters = LegendParameters()):
        self.params = params

    def build(self):
        p = self.params

        leg = ROOT.TLegend(p.x1, p.y1, p.x2, p.y2)

        leg.SetFillColorAlpha(0, 0)
        leg.SetShadowColor(0)
        leg.SetLineWidth(0)
        leg.SetTextFont(p.font)
        leg.SetTextSize(p.text_size)
        leg.SetNColumns(p.ncolumns)

        return leg
