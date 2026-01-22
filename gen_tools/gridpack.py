"""
gridpack
---------------------------------------------------------------------
Utilities to submit gridpack creation jobs for event generation workflows.
"""
import os
import subprocess
from utils import get_logger, load_config

logger = get_logger(__name__)

def run_gridpack(
      analysis_name, 
      analysis_meta, 
      workdir,
      submit,
      process
    ):
    """
    Run gridpack generation batch jobs via Condor.
    """
    
    gen_metadata = load_config(analysis_meta["generation"])
    samples = gen_metadata["samples"]

    cwd = os.getcwd()
    for sample_metadata in samples:
      procname = sample_metadata.get("name")
      if procname != process: # Only submit  the requested process
          continue 


      logger.warning(f"Running gridpack for analysis {analysis_name}: {process}")
      outdir = os.path.join(
        workdir, 
        process
      )

      # run the gridpack: package mgcards and submit the condor job
      os.chdir( outdir )
      subprocess.run(
        [
            "tar", 
            "-zcvf", 
            "cards.tgz", 
            "mgcards"
        ], 
        check=True
      )

      if submit:
          logger.info(f"Submitting gridpack job for process {process}")
          subprocess.run(
            [
                "condor_submit", 
                "run_gridpack_batch.jds"
            ], 
            check=True
          )
      else:
        logger.info(f"Gridpack job for process {procname} is ready for submission in {outdir}")

      os.chdir( cwd )
      logger.info("Gridpack submission completed.")
