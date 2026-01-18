"""
Mode builders and registry.
Each builder is a callable that returns a function accepting an environment dict.
"""
import os
import subprocess
from utils import get_logger
from utils import load_config
logger = get_logger(__name__)

def _setup_gen():
    """Builder for setting up GEN related aspects."""
    from pathlib import Path
    from gen_tools import (
        GenerationConfig,
        _prepare_fragment,
        _prepare_gridpack,
        _setup_madgraph,
        _prepare_nanogen
    )
    from utils import (
        load_config, 
        get_operators, 
    )
    def setup_gen_config( environment ):

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
        # GEN output path on EOS
        genoutpath = os.path.join(
            environment.get('outpath'),
            environment.get("tag"),
        )
        
        config = GenerationConfig(
            measurement_name = measurement_name,
            workdir = Path( environment.get("workdir") ),
            outpath = f"{environment.get('eos_redirector')}{genoutpath}",
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
    
    return setup_gen_config

def _submit_gen():
    """Builder for setting up GEN related aspects."""
    from gen_tools import submit_gridpack, submit_nanogen
    def submit_gen( environment ):
        """Submit gridpack or nanogen generation jobs based on the environment settings."""
        what = environment.get("what") 
        submit = environment.get("submit")
        combdir = environment.get("workdir")

        # Check if the processes directory exists
        processes_path = os.path.join(combdir, "processes")
        print( os.listdir( processes_path ) )
        if not os.path.isdir(processes_path):
            logger.error(f"No 'processes' folder found in {combdir}. Run setup first.")
            return
        
        # List all folders inside processes
        process_folders = [f for f in os.listdir(processes_path) 
                          if os.path.isdir(os.path.join(processes_path, f))]
        
        if not process_folders:
            logger.error(f"No process folders found in {processes_path}")
            return
        
        # Display available folders and ask user to select
        logger.info(f"Found {len(process_folders)} process folder(s) in {processes_path}:")
        for idx, folder in enumerate(process_folders, 1):
            logger.debug(f"  {idx}. {folder}")
        
        # Get user input
        try:
            choice = input("\nSelect process folder number (or 'all' to submit all): ").strip()
            
            if choice.lower() == 'all':
                selected_folders = process_folders
            else:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(process_folders):
                    selected_folders = [process_folders[choice_idx]]
                else:
                    logger.error(f"Invalid selection. Please choose between 1 and {len(process_folders)}")
                    return
        except ValueError:
            logger.error("Invalid input. Please enter a number or 'all'")
            return
        except KeyboardInterrupt:
            logger.info("\nSubmission cancelled by user.")
            return
        
        # Submit selected folders
        for proc in selected_folders:
            proc_folder = os.path.join(processes_path, proc)
            logger.info(f"Submitting {proc}...")
            
            if what == "gridpack":
                submit_gridpack( proc_folder, submit )
            elif what == "nanogen":
                submit_nanogen( proc_folder, environment )
            else:
                logger.error(f"Unknown 'what' option: {what}. Choose between 'gridpack' or 'nanogen'.")
    return submit_gen

def _reinterpret():
    """Builder for 'reinterpret' mode."""
    from reinterpret_tools.reinterpret import reinterpret_one_measurement
    def make_reinterpretation( environment ) -> None:

        """
        Top-level entry to prepare and run a reinterpretation.
        """

        # Load the main configurations
        outpath = environment.get("outpath")
        ncores = environment.get("ncores")
        debug = environment.get("debug")
        doUnc = environment.get("doUnc")
        measurement_name = environment.get("measurement")
        measurements_path = environment.get("measurements_path")
        reinterpret_meta = load_config(
            f"{measurements_path}/{measurement_name}/reinterpretation.yml"
        )

        logger.warning(f"Setting measurement {measurement_name}")
        reinterpret_one_measurement(
            measurement_name = measurement_name,
            outpath = outpath, 
            metadata = reinterpret_meta,
            lumis = environment.get("lumis"),
            ncores = ncores,
            debug = debug,
            doUnc = doUnc
        )

        logger.info("measurement setup completed.")

    return make_reinterpretation

def _setup_combine():
    """Builder for installing combine. Executes a script inside `combine_tools`."""
    def run_combine_install(environment):
        script = f"{environment.get('mainpath')}/combine_tools/install_combine.sh"
        options = [
            # Singularity mounting points
            "singularity run",
            "-B /afs -B /eos -B /cvmfs -B /etc/grid-security -B /etc/pki/ca-trust",
            "--home $PWD:$PWD",

            # Script
            f"{environment.get('combine_image')} {script}",

            # Arguments
            "-p", environment.get('mainpath'),
            "-a", environment.get('combine_scram'),
            "-r", environment.get('combine_cmsrel'),
            "-b", environment.get('combine_comb_branch'),
            "-c", environment.get('combine_ch_branch'),
        ]

        cmd = " ".join(options)
        subprocess.check_call(
            cmd,
            shell=True,
            cwd=os.getcwd(),
        )
    
    return run_combine_install

MODE_REGISTRY = {
    # Each entry provides:
    #  - "funcs": list of builders that return a function accepting environment
    "setup": {
        "funcs": [_setup_gen],
    },
    "submit": {
        "funcs": [_submit_gen],
    },
    "reinterpret": {
        "funcs": [_reinterpret],
    },
    "setup_combine": {
        "funcs": [_setup_combine],
    },
}
