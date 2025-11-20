import ROOT
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

@dataclass
class PadConfig:
    name: str
    coords: Tuple[float, float, float, float]
    margins: Dict[str, float]

@dataclass
class CanvasParameters:
    """Configuration for a ROOT canvas layout."""
    x_size: int = 600
    y_size: int = 600
    top_spam_size: float = 1.1
    pads: List[PadConfig] = field(default_factory=list)

    @classmethod
    def with_ratio(cls):
        """Two pads: main + ratio."""
        return cls(
            pads=[
                PadConfig("main", (0, 0.25, 1, 1),
                          dict(top=0.055, bottom=0.025, left=0.16, right=0.03)),
                PadConfig("ratio", (0, 0, 1, 0.25),
                          dict(top=0.06, bottom=0.42, left=0.16, right=0.03)),
            ]
        )

    @classmethod
    def single_pad(cls) :
        """Single pad (no ratio)."""
        return cls(
            pads=[
                PadConfig("main", (0, 0, 1, 1),
                          dict(top=0.05, bottom=0.12, left=0.14, right=0.03))
            ]
        )

class CanvasBuilder:
    """Builds ROOT.TCanvas objects from a CanvasConfig."""

    def __init__(self, config: CanvasParameters):
        self.config = config

    def build(self, name: str):
        cfg = self.config

        npads = len(cfg.pads)

        # Create canvas
        canvas = ROOT.TCanvas(name, "", cfg.x_size, cfg.y_size)

        # Adjust top margin using spam scaling factor
        canvas.SetTopMargin(canvas.GetTopMargin() * cfg.top_spam_size)

        # Create subpads if needed
        if npads > 1:
            canvas.Divide(1, npads)

        pads = {} # This way root does not delete it

        # Configure each pad
        for i, pad_cfg in enumerate(cfg.pads, start=1):

            pad = canvas.GetPad(i) if npads > 1 else canvas

            x0, y0, x1, y1 = pad_cfg.coords
            pad.SetPad(x0, y0, x1, y1)

            pad.SetTopMargin(pad_cfg.margins["top"])
            pad.SetBottomMargin(pad_cfg.margins["bottom"])
            pad.SetLeftMargin(pad_cfg.margins["left"])
            pad.SetRightMargin(pad_cfg.margins["right"])

            pads[pad_cfg.name] = pad

        return canvas, pads
