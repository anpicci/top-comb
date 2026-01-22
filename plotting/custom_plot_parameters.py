""" This class serves as an interface between the user and the other plotting classes. """
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class CustomPlotParameters:
    """Holds configurable plot parameters."""
    xTitle: str = "X-axis"
    yTitle: str = "Y-axis"
    logy: bool = False
    annotations: List = None 
    lines: List[ Dict ] = None
    xBinLabels: List[str] = None
    RatioRange: Optional[ Tuple[float, float] ] = (0.8, 1.2)

    @classmethod
    def from_dict( cls, config_dict: Dict ) -> "CustomPlotParameters":
        return cls( **config_dict )
