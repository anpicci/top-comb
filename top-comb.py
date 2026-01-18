import os
import argparse
import sys
from utils.logger import get_logger
from environment import TopCombEnv
from modes import MODE_REGISTRY
from utils import load_config, prepare_workdir 
logger = get_logger(__name__)

def run_pipeline(mode_info, environment):
    """
    Execute all functions belonging to the mode.
    Each element in mode_info["funcs"] is a builder that returns a function.
    """
    funcs = mode_info.get("funcs", [])
    for builder in funcs:
        func = builder()
        func(environment)

def add_setup_parser(subparsers):
    """Register subcommands for setup modes."""
    setup_parser = subparsers.add_parser("setup", help="Prepare code for generating gridpacks and nanogen inputs.")
    setup_parser.add_argument("-m", "--measurement", default="dummy", help="Measurement configurations to be setup")

def add_submit_gen_parser(subparsers):
    """Register subcommands for setup modes."""
    submit_gen_parser = subparsers.add_parser("submit", help="Prepare code for generating gridpacks and nanogen inputs.")
    submit_gen_parser.add_argument("-w", "--what", default="gridpack", help="Choose between: gridpack/nanogen")
    submit_gen_parser.add_argument("-s", "--submit", default=False, action = "store_true", help="Actually submit or dry run.")
    submit_gen_parser.add_argument("-j", "--njobs", default = 5000, help="How many jobs to submit.")
    submit_gen_parser.add_argument("-n", "--nevents-per-job", dest = "nevents_per_job", default = 200, help="How many nanogen events are run per jobs.")
    
def add_reinterpret_parser(subparsers):
    """Add options for reinterpretation."""
    reinterpret_parser = subparsers.add_parser("reinterpret", help="Run the reinterpretation of differential measurements.")
    reinterpret_parser.add_argument("-m", "--measurement", default="dummy", help="Measurement configurations to be setup")
    reinterpret_parser.add_argument('--ncores', default=12, type=int, help="Number of cores to run with.")
    reinterpret_parser.add_argument('--do-unc', dest="do_unc", action="store_true", default=False, help="Turn on systematic variations.")
    reinterpret_parser.add_argument('--just-replot', dest="replot", action="store_true", default=False, help="Just replot, don't run the analysis")
    reinterpret_parser.add_argument('--debug', action="store_true", default=False, help="Activate debug compiler flags for custom modules")


def add_combine_parser(subparsers):
    """Add options for combine."""
    combinesetup_parser = subparsers.add_parser("setup_combine", help="Install the combine release.")

def main():
    parser = argparse.ArgumentParser(description="Main parser for the top-comb.py script.")
    parser.add_argument("--outpath", default=None, type=str, help="Where to store results.")
    parser.add_argument("--config", default="main.yml", type=str, help="Path to config file")
    parser.add_argument("--tag", default="myrun", type=str, help="Workdir tag folder to use")
    
    subparsers = parser.add_subparsers(dest="mode")
    add_setup_parser(subparsers)
    add_submit_gen_parser(subparsers)
    add_reinterpret_parser(subparsers)
    add_combine_parser(subparsers)

    args = parser.parse_args()

    # Validate mode early
    if not args.mode:
        logger.error("No mode provided. Available modes: setup, reinterpret, setup_combine")
        sys.exit(1)

    if args.mode not in MODE_REGISTRY:
        logger.error(f"Unknown mode '{args.mode}'. Available modes: {', '.join(MODE_REGISTRY.keys())}")
        sys.exit(1)

    # Build environment configuration
    env_kwargs = {"outpath": args.outpath} if args.outpath is not None else {}
    top_env = TopCombEnv.new(**env_kwargs)
    env_settings = top_env.model_dump()
    
    environment = {
        **vars(args),
        **env_settings,
    }

    # Load configuration and update environment
    main_config = load_config(environment["config"])
    workdir = os.path.join(environment["workdir"], environment["tag"])
    
    environment["main_config"] = main_config
    environment["workdir"] = workdir

    # Prepare workdir for setup mode
    if args.mode == "setup":
        prepare_workdir(environment)

    # Execute the pipeline for the selected mode
    run_pipeline(
        mode_info=MODE_REGISTRY[args.mode],
        environment=environment
    )


if __name__ == "__main__":
    main()
