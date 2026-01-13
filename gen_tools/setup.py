"""
Setup
---------------
Helpers to prepare MadGraph cards, fragments and submission scripts for
event generation workflows.
"""
from pathlib import Path
from environment import TopCombEnv

from .generation_config import GenerationConfig
from .madgraph_utils import _setup_madgraph
from .gridpack_utils import _prepare_gridpack
from .fragment_utils import _prepare_fragment
from .nanogen_utils import _prepare_nanogen

from utils import (
    load_config, 
    get_operators, 
    get_logger
)


logger = get_logger(__name__)

# ============================================================
# Main Entry Point
# ============================================================
def setup_gen_config(
        environment: TopCombEnv 
    ) -> None:

    """
    Create generation work directories and prepare MadGraph configuration.
    """
    
    # Load the main configurations and select the ones for an
    # specific measurement
    main_config = environment.get("main_config")["MEASUREMENTS"]
    measurement_name = environment.get("measurement")
    measurement_config = main_config.get( measurement_name )
    
    # Load generation metadata
    measurements_path = environment.get("measurements_path")
    gen_metadata = load_config( f"{measurements_path}/{measurement_name}/generation.yml" )
    operators = get_operators( measurement_config.get("operators") )

    # Use the helper class to propagate the information a bit more efficiently
    config = GenerationConfig(
        measurement_name = measurement_name,
        workdir = Path( environment.get("workdir") ),
        outpath = environment.get("outpath"),
        mcprod_path = environment.get("mcprod"),
        genprod_image = environment.get("genproductions_image"),
        genprod_repo = environment.get("genproductions_repo"),
        genprod_branch = environment.get("genproductions_branch")
    )

    # Process each sample
    samples = gen_metadata["samples"]
    for proc_metadata in samples:
        _setup_madgraph( proc_metadata, operators, config )
        _prepare_fragment( proc_metadata, config)
        _prepare_gridpack( proc_metadata, config )
        _prepare_nanogen( proc_metadata, config )