"""
gridpack
---------------------------------------------------------------------
Utilities to submit gridpack creation jobs for event generation workflows.
"""
import os
import subprocess
import utils.auxiliars as aux
from utils import get_logger, load_config

logger = get_logger(__name__)


def run_gridpack(analysis_name, analysis_meta, workdir, settings):
    """
    Run gridpack generation batch jobs via Condor.
    - For each sample:
      * Load sample metadata and determine the output directory.
      * Create a tarball of the 'mgcards' directory as cards.tgz.
      * Submit the Condor job.
    """
    
    gen_metadata = load_config(analysis_meta["generation"])
    logger.warning(f"Running gridpack for analysis {analysis_name}")
    samples = gen_metadata["samples"]

    for sample_metadata in samples:
        procname = sample_metadata["name"]
        outdir = os.path.join(workdir, procname)

        # run the gridpack: package mgcards and submit the condor job
        os.chdir(outdir)
        subprocess.run(["tar", "-zcvf", "cards.tgz", "mgcards"], check=True)
        subprocess.run(["condor_submit", "run_gridpack_batch.jds"], check=True)
        os.chdir(settings['topcomb_mainpath'])

    logger.info("Gridpack submission completed.")
