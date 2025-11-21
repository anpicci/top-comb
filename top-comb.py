import os
import sys
from utils.parser import main_parser 
from utils.logger import get_logger
from environment import TopCombEnv
from modes import MODE_REGISTRY
from utils import load_config, prepare_workdir 
logger = get_logger(__name__)

def run_per_analysis(analyses, func, inputs):
    for analysis_name, analyses_meta in analyses.items():
        inputs["analysis_name"] = analysis_name
        inputs["analysis_meta"] = analyses_meta
        func( **inputs )

def run_pipeline(mode_info, environment):
    """
    Execute all functions belonging to the mode.
    Each element in mode_info["funcs"] is a callable returning (func, inputs).
    """

    funcs = mode_info.get("funcs", [])
    per_analysis = mode_info.get("per-analysis", False)

    for builder in funcs:
        # builder builds the function + inputs for THIS step
        func, inputs = builder( environment )

        if per_analysis:
            analyses = environment.get("main_config")["analyses"]
            run_per_analysis(
                analyses = analyses,
                func = func,
                inputs = inputs,
            )
        else:
            func( **inputs )

def main():
    parser, _ = main_parser()
    args = parser.parse_args()

    if not args.mode:
        logger.error("No mode provided. Use --mode.")
        sys.exit(1)

    # ----------------------------------------------
    # Pack all the inputs in a single dictionary. Then
    # pass that environment to the different modes.
    # There are some parameters that can be modified by users
    env_settings = TopCombEnv.new( {} )
    if args.outpath != None:
        env_settings = TopCombEnv.new( 
            outpath = args.outpath,
        )
    environment = {
        **env_settings,
        **vars(args),
    }

    main_config = load_config( 
        environment.get("main_config") 
    )
    
    workdir = os.path.join(
        environment.get("workdir"), 
        environment.get("tag") 
    )
    
    environment["main_config"] = main_config
    environment["workdir"] = workdir
    # ----------------------------------------------

    # ----------------------------------------------
    # Now prepare running things
    mode = environment.get("mode")
    if mode == "setup":
        prepare_workdir(
            environment = environment,
        )
    run_pipeline(
        mode_info = MODE_REGISTRY[ mode ],
        environment = environment
    )
    # ----------------------------------------------


if __name__ == "__main__":
    main()
