
""" Class to handle things that are required by the combination code """
from environment import TopCombEnv
from .auxiliars import (
    load_config, 
    get_logger,
)

from .json_to_root import read_json_histograms
import json
from .hepdata_to_root import (
    read_hepdata_to_graph,
    read_hepdata_to_th1
)


logger = get_logger(__name__)


from components import ttgamma_component


class CombinationChef:
    """Class to handle things that are required by the combination code."""

    components = {
        "ttgamma" : ttgamma_component
}
    def __init__(
            self, 
            measurement_name: str, 
            observable: str,
            config_path: str,
            environment: TopCombEnv,
            ):

            self.measurement_name = measurement_name
            self.observable = observable
            self.config_path = config_path
            self.environment = environment

            logger.info(f"Using configuration from {config_path}")
            self.observable_config = load_config( self.config_path )

            component = self.components.get( self.measurement_name )
            inputs = self.observable_config.get("components", {})
            
            component_inst = component(
                dataset = self.observable_config.get("dataset", ""),
                **inputs
            )

            measurement = component_inst.prepare_measurements()
            measurement.writeToJSON(
                f"eftcomb/measurements/CMS_{self.measurement_name}.json"
            )

            eftscaling = component_inst.prepare_scalings()
            with open(f"eftcomb/scalings/CMS_{self.measurement_name}_scalings.json", "w") as f:
                json.dump(eftscaling, f, indent=4)
            

    def _prepare_measurement_jsons(self):
        """
        The measurement json containes the following structure:

        {
            "nbins" : int # number of bins in the observable
            "bf" : List[float] # best fit values for each bin
            "bf_unc" : List[float] # uncertainties on the best fit values for each bin
            "cov" : List[List[float]] # covariance matrix for the bins
            "cov_th": List[List[float]] # theory covariance matrix for the bins
            "cov_hessian": List[List[float]] # hessian covariance matrix for the bins
            "sm": List[float] # standard model prediction for each bin
            "sm_unc": List[float] # uncertainties on the standard model prediction for each bin
            "bin_labels": List[str] # labels for each bin
        }

        This function should only require a hepdata yaml file where from where to extract the
        values.
        """

        

