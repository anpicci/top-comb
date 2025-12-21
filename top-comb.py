import os
import sys
from utils.parser import main_parser 
from utils.logger import get_logger
from environment import TopCombEnv
from modes import MODE_REGISTRY
from utils import load_config, prepare_workdir 
logger = get_logger(__name__)

def run_pipeline(mode_info, environment):
    """
    Execute all functions belonging to the mode.
    Each element in mode_info["funcs"] is a callable returning (func, inputs).
    """
    funcs = mode_info.get("funcs", [])
    for builder in funcs:
        # builder builds the function + inputs for THIS step
        func = builder()
        func( environment )

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
    top_env = TopCombEnv.new( **{} )
    if args.outpath != None:
        top_env = TopCombEnv.new( 
            outpath = args.outpath,
        )

    env_settings = top_env.model_dump()
    environment = {
        **vars(args),
        **env_settings,
    }

    main_config = load_config( 
        environment.get("config") 
    )
    
    workdir = os.path.join(
        environment.get("workdir", ""), 
        environment.get("tag", "") 
    )
    
    environment["main_config"] = main_config
    environment["workdir"] = workdir
    # ----------------------------------------------

    # ----------------------------------------------
    # Now prepare running things
    mode = environment.get("mode")
    if not mode:
        logger.error("No mode found in environment.")
        sys.exit(1)

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
