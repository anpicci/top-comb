"""
gridpack
---------------------------------------------------------------------
Utilities to submit gridpack creation jobs for event generation workflows.
"""
from .utils import write_text
from pathlib import Path
from typing import Dict, Any
import os
import subprocess

from utils import (
    open_template, 
    get_logger
)

logger = get_logger(__name__)

def _get_gridpack_path(
        outpath: str,
        measurement_name: str,
        procname: str
    ) -> str:
    """
    Construct gridpack path with redirector removed.
    """
    gridpacks_base = f"{outpath}/{procname}"
    # Remove any redirectors from the fragment path
    gridpacks_base = gridpacks_base.replace("root://eosuser.cern.ch/", "")
    return f"{gridpacks_base}/gridpack.tar.xz"


def _prepare_gridpack(
        measurement_name: str,
        proc_metadata: Dict[str, Any],
        outpath: Path,
        procdir: Path,
        genprod_image:str,
        genprod_repo:str,
        genprod_branch:str,
    ):

    """
    Prepare everything to run gridpacks on HTCondor.
    """
    procname = proc_metadata["name"]

    _create_gridpack_scripts(
        measurement_name,
        proc_metadata,
        outpath,
        procdir,
        genprod_image,
        genprod_repo,
        genprod_branch
    )
    
    cwd = os.getcwd()

    # run the gridpack: package mgcards and submit the condor job
    os.chdir( procdir )
    subprocess.run(
      [
          "tar", 
          "-zcvf", 
          "cards.tgz", 
          "mgcards"
      ], 
      check=True
    )
    logger.info(f"Gridpack job for process {procname} is ready for submission in {procdir}")
    os.chdir( cwd )

    return _get_gridpack_path(
        outpath,
        measurement_name,
        procname
    )

def _create_gridpack_scripts(
        measurement_name: str,
        metadata: Dict[str, Any],
        outpath: str,
        mgworkdir: Path,
        genprod_image: str,
        genprod_repo: str,
        genprod_branch: str
    ) -> None:

    """
    Create helper scripts to run the gridpack creation and submission.
    """
    procname = metadata["name"]
    mgworkdir = Path(mgworkdir)

    # Create bash wrapper script
    bash_content = _render_gridpack_bash_script(
        procname,
        measurement_name,
        genprod_image,
        genprod_repo,
        genprod_branch
    )
    write_text(mgworkdir / "run_gridpack_batch.sh", bash_content)

    # Create condor submission file
    jds_content = _render_condor_submission_file(procname, outpath)
    write_text(mgworkdir / "run_gridpack_batch.jds", jds_content)


def _render_gridpack_bash_script(
        procname: str,
        measurement_name: str,
        genprod_image: str,
        genprod_repo: str,
        genprod_branch: str
    ) -> str:

    """
    Create bash script for gridpack generation.
    """

    template = open_template("templates/run_gridpack_batch.sh")
    substitutions = {
        "__PROCNAME__": procname,
        "__measurement_NAME__": measurement_name,
        "__CARDSDIR__": "mgcards",
        "__SINGULARITY_IMAGE__": genprod_image,
        "__GENPRODUCTIONS_GRIDPACK__": genprod_repo,
        "__BRANCH_GRIDPACK__": genprod_branch,
    }

    for placeholder, value in substitutions.items():
        template = template.replace(placeholder, value)
    
    return template

def _render_condor_submission_file(procname: str, outpath: str) -> str:
    """
    Render condor submission description file.
    """
    template = open_template("templates/template_submit.jds")
    
    substitutions = {
        "__SCRIPTNAME__": "run_gridpack_batch.sh",
        "__OUTPATH__": f"{outpath}/{procname}",
        "__PROCNAME__": f"{procname}_runGridpack",
        "__NCORES__": "8",
    }

    for placeholder, value in substitutions.items():
        template = template.replace(placeholder, value)
    
    return template