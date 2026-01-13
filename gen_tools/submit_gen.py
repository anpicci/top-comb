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

    process = proc_folder.split("/")[-1]
    cmd = [
        "python3", 
        "mc-prod/main.py", 
        f"--process {process}", 
        "--mode nanogen",
        "--backend condor", 
        "--submit"
    ]
    if environment.get("submit", False):
        os.chdir( proc_folder )
        subprocess.run(
            cmd,
            check=True
        )
        os.chdir( cwd )
    else:
        logger.info(f"Dry-run: would submit nanogen generation in {proc_folder}")
        logger.info(f"To submit, run: {' '.join(cmd)}")

def submit_gen( environment ):
    """Submit gridpack or nanogen generation jobs based on the environment settings."""
    input = environment.get("input") 
    what = environment.get("what") 
    submit = environment.get("submit")

    # Guess how many inputs do we have, can be:
    # The folder with different processes (e.g. ttgamma has two processes
    # one with ttG from decay, or from production)

    is_this_workdir = os.path.exists( os.path.join( input, "processes") )

    if is_this_workdir:
        logger.info(f"Found 'processes' folder inside {input}, assuming it's a workdir with multiple processes.")
        process_folders = os.listdir( os.path.join( input, "processes") ) 

        for proc in process_folders:
            proc_folder = os.path.join( input, "processes", proc )
            if what == "gridpack":
                submit_gridpack( proc_folder, submit )
            elif what == "nanogen":
                submit_nanogen( proc_folder, environment )
            else:
                logger.error(f"Unknown 'what' option: {what}. Choose between 'gridpack' or 'nanogen'.")

