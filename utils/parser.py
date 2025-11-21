
import argparse

def main_parser():
    """Create and return the main argument parser."""
    parser = argparse.ArgumentParser(description="Main parser for the top-comb.py script.")

    parser.add_argument("--config", default="main.yml", type=str, help="Path to config file")
    parser.add_argument("--tag", default="myrun", type=str, help="Workdir tag folder to use")

    subparsers = parser.add_subparsers( dest="mode" )
    add_subcommands( subparsers )
    return parser, subparsers


def add_subcommands(subparsers):
    """Register subcommands for setup modes."""
    setup_parser = subparsers.add_parser("setup", help="Prepare code for generating gridpacks and nanogen inputs.")
    setup_parser.add_argument("--reset", default=False, help="Remove old directory and remake it", action="store_true")
    
    run_gridpack_parser = subparsers.add_parser("run_gridpack", help="Submit gridpacks to condor.")
    run_nanogen_parser = subparsers.add_parser("run_nanogen", help="Submit generation of NanoGEN outputs to condor.")

    # Add options for reinterpretation
    reinterpret_parser = subparsers.add_parser("reinterpret", help="Run the reinterpretation of differential measurements.")
    reinterpret_parser.add_argument( '--select-flow',   dest = "select_flow",  default = "validation",  help = "Kind of flow one wants to run." )
    reinterpret_parser.add_argument( '--ncores', dest = "ncores",  default = 12, type = int, help = "Number of cores to run with." )
    reinterpret_parser.add_argument( '--doUnc',  dest = "doUnc",  default = True, action = "store_true", help = "Turn on systematic variations." )
    reinterpret_parser.add_argument( '--just-replot',  dest = "replot",  action = "store_true", default = False, help = "Just replot, don't run the analysis" )
    reinterpret_parser.add_argument( '--debug',  dest = "debug",  action = "store_true", default = False, help = "Activate debug compiler flags for custom modules" )