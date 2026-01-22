import sys
from environment import TopCombEnv
import numpy as np

mainpath = TopCombEnv().mainpath
sys.path.insert(0, mainpath)  # toplevel path


from utils import (
    load_config,
    components,
    get_logger
)

from utils.hepdata_to_root import (
    read_hepdata_to_th1,
    read_hepdata_to_graph
)

from eftcomb.python.tools import (
    Measurement
)

logger = get_logger(__name__)

class ttgamma_component(components.component):
    """
    A component specific for the ttgamma combination measurement.
    Inherits from the generic component class.

    Attributes:
        dataset (str): The dataset name (e.g., "Run2").
        central_values (str): Path to the central values file.
        total_cov (str): Path to the total covariance matrix file.
        stat_cov (str): Path to the statistical covariance matrix file.
    """


    bin_label_format = "ttg_pho1pt_{ibin}" 
    
    def prepare_measurements(self) -> Measurement:
        """
        Prepare the measurement inputs specific to the ttgamma analysis.
        This method can be extended to include reading specific files,
        processing data, and setting up histograms or graphs as needed.
        """
        logger.info(f"Preparing ttgamma measurements for TTGamma analysis")


        # The observed is read from the first column in the hepdata
        datavalues, datalabels = components.component.read_hepdata(
            self.central_values,
            group_index=0
        )
        
        dataerrors, _ = components.component.read_hepdata(
            self.central_values,
            group_index=0,
            error = [0,1],
        )

        data_totalcorr, _ = components.component.read_hepdata(
            self.total_cov,
            group_index=0
        )

        # Convert correlation matrix to covariance matrix
        nbins = len(datavalues)
        data_totalcov = np.zeros( (nbins, nbins) )

        data_totalcorr_reshape = data_totalcorr.reshape( (nbins, nbins) )
        for i in range( nbins ):
            for j in range( nbins ):
                data_totalcov[i][j] = data_totalcorr_reshape[i][j] * dataerrors[i] * dataerrors[j]

        sm, smlabels = components.component.read_hepdata(
            self.central_values,
            group_index=2
        )

        bf = datavalues / sm
        bf_unc = dataerrors / sm

        measurement = Measurement(
            nbins = nbins,
            bin_labels = self.get_bin_labels( nbins ),
            sm = sm,
            sm_unc = np.zeros_like(sm),
            bf = bf,
            bf_unc = bf_unc,
            cov = data_totalcov
        )

        return measurement

    def prepare_scalings(self) -> dict:
        """
        Prepare the EFT scaling specific to the ttgamma analysis.
        This method can be extended to include reading specific files,
        processing data, and setting up scaling functions as needed.
        """
        logger.info(f"Preparing ttgamma EFT scalings for TTGamma analysis")

        # Read the EFT shapes
        mapping = load_config( self.mapping )

        # convert the mapping to something EFT2obs can use for scaling
        smhepdata, smlabels = components.component.read_hepdata(
            self.central_values,
            group_index=2
        )

        filter_histograms = [ 
            f"TTGEFT__{opname}" for opname in mapping.keys() 
        ]
        
        shapes = components.component.read_cmgrdf_shapes( 
            self.eftshapes,
            filter_histograms = filter_histograms
        )

        sm = components.component.read_cmgrdf_shapes(
            self.eftshapes,
            filter_histograms = [ "TTGEFT__SM" ]
        )["TTGEFT__SM"]

        ret = {
            "bin_labels" : self.get_bin_labels( len(sm) ),
            "terms" : [],
            "parameters" : [],
            "nbins" : len(smlabels),
            "bin_edges" : smlabels,
            "sm_vals" : smhepdata.tolist(),
        }

        
        for shape in shapes.values():
            # Let's skip these for the moment
            if "minus" in shape.GetName() or "SM" in shape.GetName():
                continue
            term = shape.GetName().split("__")[-1]

            op_list = term.split("_")

            if len(op_list) == 1:
                op_name = op_list[0].replace("1p0", "")
                if op_name not in mapping:
                    ret["parameters"].append( op_name )

            opnames = [
                op.replace("1p0", "") for op in op_list 
            ]

            scaling = [
                opnames,
                [], # Central values
                [], # errors
            ] 
        
            for ibin in range(1, shape.GetNbinsX() + 1):
                bin_content = shape.GetBinContent(ibin)
                bin_error = shape.GetBinError(ibin)

                # Divide by lumi
                bin_content /= TopCombEnv().lumis[ self.dataset]
                bin_error /= TopCombEnv().lumis[ self.dataset]


                # Divide by width
                bin_width = shape.GetXaxis().GetBinWidth(ibin)
                bin_content /= bin_width
                bin_error /= bin_width

                sm_content = sm.GetBinContent(ibin)
                sm_content /= TopCombEnv().lumis[ self.dataset]
                sm_content /= bin_width

                if sm != 0:
                    # scaling[1].append(bin_content / sm[ibin-1])
                    # scaling[2].append(bin_error / sm[ibin-1]) # No error for the moment
                    scaling[1].append(bin_content / sm_content )
                    scaling[2].append(bin_error / sm_content )
                else:
                    scaling[1].append(ibin, 0.0)
                    scaling[2].append(ibin, 0.0)

                
            ret["terms"].append( scaling )  
            
        return ret
