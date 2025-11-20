"""
nanogen
-------
Helpers to run NanoGen validation for generated samples.
"""
import os
import subprocess
from utils import get_logger, load_config

from settings import TopCombSettings
settings = TopCombSettings().model_dump()
logger = get_logger(__name__)


def run_nanogen(analysis_name, analysis_meta, workdir, settings):
    """
    Run NanoGen validation for each configured process using tmg-tools.
    """
    gen_metadata = load_config(analysis_meta["generation"])
    logger.warning(f"Running NanoGen for analysis {analysis_name}")
    samples = gen_metadata["samples"]
    for sample_metadata in samples:
        procname = sample_metadata["name"]
        outdir = os.path.join(workdir, procname)

        script = os.path.join(settings["topcomb_tmgtools"], "main.py")
        jsonfile = os.path.join(outdir, "nanogen_config.json")

        subprocess.run(["python3", script, "--parse_from_json", jsonfile, "--mode", "nanogen", "--submit"])

    logger.info("NanoGen execution completed.")
