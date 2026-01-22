"""
Mode builders and registry.
Each builder is a callable that returns a function accepting an environment dict.
"""
import os
import subprocess
from utils import (
    get_logger,
    load_config,
    create_dir

)
logger = get_logger(__name__)

def _setup():
    """Builder for setting up GEN related aspects."""
    from pathlib import Path
    from gen_tools import (
        madgraph_utils,
        gridpack_utils,
        fragment_utils,
        nanogen_utils,
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
            "gridpacks",
        )
        
        # Setup the common part (reweighting maps and whatnot)
        measurement_dir = Path(environment.get("workdir")) / measurement_name
        os.makedirs( measurement_dir , exist_ok=True )
        rwgt_points = madgraph_utils._generate_reweight_points(
            operators
        )

        # Save a mapping json tied to the measurement phase space
        madgraph_utils._build_reweight_mapping(
            measurement_dir,
            rwgt_points,
            operators
        )

        # Save also a README for quick view in gitlab
        madgraph_utils._build_reweight_readme(
            measurement_dir,
            rwgt_points,
            operators
        )

        ## Process each sample
        samples = gen_metadata["samples"]
        for proc_metadata in samples:

            # Prepare the process directory
            procname = proc_metadata["name"]
            restrict_name = proc_metadata["template_restrict_card"]["restrict_name"]
            procdir = measurement_dir / "mcgen" / proc_metadata["name"]
            create_dir( procdir )
            create_dir( procdir / "mgcards" )
            files = [
                ( procdir / "mgcards" / f"{procname}_proc_card.dat" , madgraph_utils.prepare_proc_card( proc_metadata ) ),
                ( procdir / "mgcards" / f"{procname}_run_card.dat" , madgraph_utils.prepare_run_card( proc_metadata ) ),
                ( procdir / "mgcards" / f"{procname}_extramodels.dat" , madgraph_utils.prepare_extramodels( proc_metadata ) ),
                ( procdir / "mgcards" / f"{procname}_customizecards.dat" , madgraph_utils.prepare_customizecards( proc_metadata, operators ) ),
                ( procdir / "mgcards" / f"{procname}_restrict_{restrict_name}.dat" , madgraph_utils.prepare_restrict_card( proc_metadata, operators ) ),
                ( procdir / "mgcards" / f"{procname}_reweight_card.dat" , madgraph_utils.prepare_reweightcards( rwgt_points ) ),

            ]

            for card_path, card_content in files:
                card_path.parent.mkdir(parents=True, exist_ok=True)
                with open( card_path, "w") as card_file:
                    card_file.write( card_content )
            

            # Prepare scripts and configurations
            redirector = environment.get("eos_redirector")
            gridpack_location = gridpack_utils._prepare_gridpack(
                measurement_name,
                proc_metadata,
                f"{redirector}{genoutpath}",
                procdir,
                environment.get("genproductions_image"),
                environment.get("genproductions_repo"),
                environment.get("genproductions_branch")
            ) 

            fragment_path = procdir / "fragment.py" 
            fragment_content = fragment_utils._prepare_fragment( gridpack_location, proc_metadata ) 
            with open( fragment_path, "w" ) as fragment_file:
                fragment_file.write( fragment_content )

            
            # Finally, prepare the nanogen configuration
            nanogen_utils._prepare_nanogen(
                procdir=str(procdir),
                mcprod_path=environment.get("mcpath"),
                proc_metadata=proc_metadata,
            )
    
    return setup_gen_config

def _submit_gen():
    """Builder for setting up GEN related aspects."""
    from gen_tools import submit_gridpack, submit_nanogen
    def submit_gen( environment ):
        """Submit gridpack or nanogen generation jobs based on the environment settings."""
        what = environment.get("what") 
        submit = environment.get("submit")
        combdir = environment.get("workdir")
        measurement_name = environment.get("measurement")

        # Check if the processes directory exists
        processes_path = os.path.join(combdir, measurement_name, "mcgen")
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
        reinterpretoutpath = os.path.join(
            environment.get('outpath'),
            environment.get("tag"),
            "shapes",
        )
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
            outpath = reinterpretoutpath, 
            metadata = reinterpret_meta,
            lumis = environment.get("lumis"),
            ncores = ncores,
            debug = debug,
            doUnc = doUnc
        )

        logger.info("measurement setup completed.")

    return make_reinterpretation

def _cook():
    """Builder for 'reinterpret' mode."""
    def cook_inputs( environment ) -> None:

        """
        Top-level entry to prepare the inputs for the combination,
        based on the results of the reinterpretation.
        """
        main_config = environment.get("main_config")["MEASUREMENTS"]
        measurement_name = environment.get("measurement")
        measurement_config = main_config.get( measurement_name )
        observable = measurement_config.get("observable")

        logger.info(f"Preparing inputs for measurement {measurement_name}, observable {observable}")

        config_path = os.path.join(
            "measurements",
            measurement_name,
            "observable_configs",
            f"{observable}.yaml"
        )
        from utils.combination_chef import CombinationChef
        chef = CombinationChef(
            measurement_name=measurement_name,
            observable=observable,
            config_path=config_path,
            environment=environment,
        )

        

    return cook_inputs 

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
        "funcs": [_setup],
    },
    "submit": {
        "funcs": [_submit_gen],
    },
    "reinterpret": {
        "funcs": [_reinterpret],
    },
    "cook": {
        "funcs": [_cook],
    },
    "setup_combine": {
        "funcs": [_setup_combine],
    },
}
