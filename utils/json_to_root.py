"""
Module to convert JSON histogram data to ROOT histograms.
"""

import json
import ROOT
from typing import Dict, List, Union
from plotting.cms_palette import *

class JSONtoROOTConverter:
    """
    Converts JSON histogram data to ROOT TH1D histograms.
    """
    
    def __init__(self, json_path: str):
        """
        Initialize the converter with a JSON file.
        """
        self.json_path = json_path
        self.filename = json_path.split("/")[-1].replace(".json", "")
        self.data = self._load_json()
        self.histograms = {}
        
    def _load_json(self) -> Dict:
        """Load JSON data from file."""
        with open(self.json_path, 'r') as f:
            return json.load(f)
    
    def _create_histogram(self, histo_name: str, histo_data: Dict) -> ROOT.TH1D:
        """
        Create a ROOT TH1D histogram from JSON data.
        """
        # Extract bin edges
        bins = histo_data['axes']['x']['bins']
        nbins = len(bins) - 1
        
        # Create histogram with variable binning
        hist = ROOT.TH1D(
            histo_name,
            histo_name,
            nbins,
            bins[0],
            bins[-1]
        )
        
        # Set axis titles
        x_title = histo_data['axes']['x'].get('title', '')
        y_title = histo_data['axes']['y'].get('title', '')
        hist.GetXaxis().SetTitle(x_title)
        hist.GetYaxis().SetTitle(y_title)
        
        # Apply style options if present
        style = histo_data['style']
        hist.SetLineColor(style['fillcolor'])
        hist.SetLineWidth(2)
        
        # Fill histogram with central values and errors
        central = histo_data['central']
        values = central['values']
        errors = central['errors']
        
        # Fill bins (ROOT bins start at 1, values array includes underflow/overflow)
        for i, (val, err) in enumerate(zip(values, errors)):
            hist.SetBinContent(i, val)
            hist.SetBinError(i, err)
        
        return hist
    
    def convert_all(self) -> Dict[str, ROOT.TH1D]:
        """
        Convert all histograms in the JSON file to ROOT histograms.
        """
        if 'histos' not in self.data:
            raise ValueError("JSON file does not contain 'histos' key")
        
        self.histograms = {}
        for histo_name, histo_data in self.data['histos'].items():
            self.histograms[histo_name] = self._create_histogram( f"{self.filename}__{histo_name}", histo_data)
        
        return self.histograms
    
    def convert_single(self, histo_name: str) -> ROOT.TH1D:
        """
        Convert a single histogram by name.
        """
        if histo_name not in self.data['histos']:
            raise ValueError(f"Histogram '{histo_name}' not found in JSON data")
        
        hist = self._create_histogram(histo_name, self.data['histos'][histo_name])
        self.histograms[histo_name] = hist
        return hist
    
    def save_to_root_file(self, output_path: str):
        """
        Save all converted histograms to a ROOT file.
        """
        if not self.histograms:
            self.convert_all()
        
        root_file = ROOT.TFile(output_path, "RECREATE")
        for name, hist in self.histograms.items():
            hist.Write()
        root_file.Close()
        print(f"Saved {len(self.histograms)} histograms to {output_path}")
    
    def get_histogram(self, histo_name: str) -> Union[ROOT.TH1D, None]:
        """
        Get a specific histogram (convert if not already done).
        """
        if histo_name in self.histograms:
            return self.histograms[histo_name]
        elif histo_name in self.data.get('histos', {}):
            return self.convert_single(histo_name)
        return None
    
    def list_histograms(self) -> List[str]:
        """
        List all available histogram names in the JSON file.
        """
        return list(self.data.get('histos', {}).keys())


def read_json_histograms(json_path: str) -> Dict[str, ROOT.TH1D]:
    """
    Convenience function to read and convert all histograms from a JSON file.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        Dictionary mapping histogram names to ROOT.TH1D objects
    """
    converter = JSONtoROOTConverter(json_path)
    return converter.convert_all()
