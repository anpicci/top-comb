
""" Class to handle things that are required by the combination code """
import numpy as np
from environment import TopCombEnv
import ROOT
from .auxiliars import (
    get_logger,
    load_config
)

from .json_to_root import read_json_histograms

from .hepdata_to_root import (
    read_hepdata_to_graph,
    read_hepdata_to_th1
)

from eftcomb.python.tools import (
    ReadDependent,
    ReadIndependent
)

logger = get_logger(__name__)

class component:
    """
    A component of the combination measurement.
    This class can read inputs in hepdata or json format. 
    The json format comes from CMGRDF outputs.
    """

    def __init__(
            self,
            dataset: str,
            **kwargs
            ):
            self.dataset = dataset 
            for k, v in kwargs.items():
                setattr(self, k, v)


    def prepare_measurements(self):
        pass
    
    def get_bin_labels(self, nbins):
        return [ self.bin_label_format.format( ibin = ibin ) for ibin in range(nbins) ]

    @staticmethod    
    def read_hepdata_to_th1(json_path, group_index=0):
        """
        Read HEPData JSON file and convert to ROOT TH1D histogram.
        """
        data = load_config(json_path)
        
        if 'histos' not in data:
            raise ValueError("JSON file does not contain 'histos' key")
        
        histo_names = list(data['histos'].keys())
        if group_index >= len(histo_names):
            raise ValueError(f"Group index {group_index} out of range for available histograms")
        
        histo_name = histo_names[group_index]
        histo_data = data['histos'][histo_name]
        
        # Create histogram
        nbins = len(histo_data['bins'])
        hist = ROOT.TH1D(histo_name, histo_name, nbins, 0, nbins)
        
        for i, bin_data in enumerate(histo_data['bins']):
            bin_content = float(bin_data.get('content', 0))
            bin_error = float(bin_data.get('error', 0))
            hist.SetBinContent(i + 1, bin_content)
            hist.SetBinError(i + 1, bin_error)
        
        return hist

    @staticmethod
    def read_hepdata( json_path, group_index=0, error = None ):
        """
        Read HEPData JSON file and convert to ROOT TGraphAsymmErrors.
        """
        data = load_config(json_path)
        if error is not None:
            dependent = ReadDependent( data, col = group_index, error = error )
        else:
            dependent = ReadDependent( data, col = group_index )

        independent = ReadIndependent( data, col = 0 )

        return dependent, independent
    
    @staticmethod
    def read_cmgrdf_shapes(json_path, filter_histograms = []):
        histograms = read_json_histograms( json_path, filter_histograms = filter_histograms )
        return histograms
