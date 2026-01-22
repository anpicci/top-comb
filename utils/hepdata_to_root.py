import ROOT
from .auxiliars import get_logger, load_config
logger = get_logger(__name__)

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

def read_hepdata_to_graph(json_path, group_index=0, error_label="total uncertainty"):
    """
    Read HEPData JSON file and convert to ROOT TGraphAsymmErrors.
    """
    data = load_config(json_path)
    
    values = data.get("values", [])
    
    n_points = len(values)
    x_vals = []
    y_vals = []
    ex_low = []
    ex_high = []
    ey_low = []
    ey_high = []
    
    for point in values:
        # Extract x value (bin center)
        x_data = point.get("x", [{}])[0]
        x_low = float(x_data.get("low", 0))
        x_high = float(x_data.get("high", 0))
        x_center = (x_low + x_high) / 2.0
        x_vals.append(x_center)
        ex_low.append(x_center - x_low)
        ex_high.append(x_high - x_center)
        
        # Extract y value for the specified group
        y_groups = point.get("y", [])
        if group_index < len(y_groups):
            y_data = y_groups[group_index]
            y_val = float(y_data.get("value", 0))
            y_vals.append(y_val)
            
            # Extract errors
            errors = y_data.get("errors", [])
            err_low = 0.0
            err_high = 0.0
            
            for error in errors:
                if error_label and error.get("label") == error_label:
                    # Asymmetric error
                    if "asymerror" in error:
                        err_low = abs(float(error["asymerror"].get("minus", 0)))
                        err_high = abs(float(error["asymerror"].get("plus", 0)))
                    # Symmetric error
                    elif "symerror" in error:
                        err_val = abs(float(error.get("symerror", 0)))
                        err_low = err_val
                        err_high = err_val
                    break
            
            ey_low.append(err_low)
            ey_high.append(err_high)
        else:
            logger.warning(f"Group index {group_index} not found in point, using 0")
            y_vals.append(0.0)
            ey_low.append(0.0)
            ey_high.append(0.0)
    
    # Create TGraphAsymmErrors
    graph = ROOT.TGraphAsymmErrors(n_points)
    for i in range(n_points):
        graph.SetPoint(i, x_vals[i], y_vals[i])
        graph.SetPointError(i, ex_low[i], ex_high[i], ey_low[i], ey_high[i])
    
    # Set default style
    graph.SetMarkerStyle(20)
    graph.SetMarkerSize(1.0)
    graph.SetLineWidth(2)
    
    return graph