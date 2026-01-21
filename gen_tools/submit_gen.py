import os
import subprocess
from utils import (
    get_logger
)
logger = get_logger(__name__)

cwd = os.getcwd()
def submit_gridpack( proc_folder, do_submit ):
    """Submit gridpack generation job for a given process folder."""
    logger.info(f"Submitting gridpack generation for process folder: {proc_folder}")
    cmd = ["condor_submit", "run_gridpack_batch.jds"]
    if do_submit:
        os.chdir( proc_folder )
        subprocess.run(
            cmd,
            check=True
        )
        os.chdir( cwd )
    else:
        logger.info(f"Dry-run: would submit gridpack generation in {proc_folder}")
        logger.info(f"To submit, run: cd {proc_folder}; {' '.join(cmd)}; cd -")

def submit_nanogen( proc_folder, environment ):
    """Submit nanogen generation job for a given process folder."""
    logger.info(f"Submitting nanogen generation for process folder: {proc_folder}")
    tag = environment.get("tag")
    process = proc_folder.rstrip("/").split("/")[-1]

    outpath = f"{environment.get('outpath')}/{tag}/NANOGEN/"
    cmd = [
        "python3", 
        "mc-prod/main.py", 
        f"--process", process, 
        f"--outpath", outpath,
        "--mode", "nanogen",
        f"--nevents-per-job", str(environment.get('nevents_per_job')),
        f"--njobs", str(environment.get('njobs')),
        "--backend", "condor", 
        "--submit", 
    ]
    if environment.get("submit", False):
        subprocess.run(
            cmd,
            check=True
        )
    else:
        logger.info(f"Dry-run: would submit nanogen generation in {proc_folder}")
        logger.info(f"To submit, run: {' '.join(cmd)}")



