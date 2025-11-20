"""
nanogen
-------
Helpers to run NanoGen validation for generated samples.
"""
import os
import subprocess
import utils.auxiliars as aux
from utils.logger import get_logger

from settings import TopCombSettings
settings = TopCombSettings().model_dump()
logger = get_logger(__name__)


def run_nanogen(analysis, settings, workdir):
    """
    Run NanoGen validation for each configured process using tmg-tools.
    """

    metadata = aux.load_config(analysis)
    analysis_name = metadata["analysis_name"]
    logger.warning(f"Running NanoGen for analysis {analysis_name} ({analysis})")
    samples = metadata["generation"]["samples"]

    for sample in samples:
        proc_metadata = aux.load_config(sample)
        procname = proc_metadata["procname"]
        outdir = os.path.join(workdir, procname)

        script = os.path.join(settings["topcomb_tmgtools"], "main.py")
        jsonfile = os.path.join(outdir, "nanogen_config.json")

        subprocess.run(["python3", script, "--parse_from_json", jsonfile, "--mode", "nanogen", "--submit"])

    logger.info("NanoGen execution completed.")
