# === Standard Library Imports ===
import os
import sys


# === Project-Specific Imports ===
from utils.parser import main_parser 
from utils.logger import get_logger
from utils import load_config, prepare_workdir 
logger = get_logger(__name__)

# === Environment ===
from settings import TopCombSettings
settings = TopCombSettings().model_dump()
from modes import MODE_REGISTRY


def run_per_analysis(analyses, func, inputs):
    for analysis_name, analyses_meta in analyses.items():
        func(analysis_name, analyses_meta, **inputs)

def run_pipeline(config, mode_info, workdir, args):
    """
    Execute all functions belonging to the mode.
    Each element in mode_info["funcs"] is a callable returning (func, inputs).
    """
    funcs = mode_info.get("funcs", [])
    per_analysis = mode_info.get("per-analysis", False)

    for builder in funcs:
        # builder builds the function + inputs for THIS step
        func, inputs = builder(workdir, args)

        if per_analysis:
            run_per_analysis(
                analyses=config["analyses"],
                func=func,
                inputs=inputs,
            )
        else:
            func(**inputs)


def main():
    parser, _ = main_parser()
    args = parser.parse_args()

    if not args.mode:
        logger.error("No mode provided. Use --mode.")
        sys.exit(1)

    mode = args.mode
    if mode not in MODE_REGISTRY:
        logger.error(f"Unknown mode: {mode}")
        sys.exit(1)

    main_config = load_config(args.config)
    workdir = os.path.join(settings["topcomb_workdir"], args.tag)

    # Only setup needs to prepare the directory
    if mode == "setup":
        prepare_workdir(
            workdir = workdir,
            mode = "setup",
            reset=getattr(args, "reset", False),
        )

    # Now run the mode pipeline
    run_pipeline(
        config=main_config,
        mode_info=MODE_REGISTRY[mode],
        workdir=workdir,
        args=args,
    )


if __name__ == "__main__":
    main()
