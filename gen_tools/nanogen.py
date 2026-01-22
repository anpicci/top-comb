"""
nanogen
-------
Helpers to run NanoGen validation for generated samples.
"""
import os
import subprocess
from utils import get_logger, load_config
logger = get_logger(__name__)


def run_nanogen(
        analysis_name, 
        analysis_meta, 
        workdir, 
        tmgtools_path,
        campaign,
        submit,
        process
    ):
    
    """
    Run NanoGen validation for each configured process using tmg-tools.
    """

    gen_metadata = load_config( 
        analysis_meta["generation"] 
    )

    samples = gen_metadata["samples"]
    for sample_metadata in samples:
        procname = sample_metadata["name"]

        if procname != process: # Only submit  the requested process
            continue
    
        logger.info(f"Running NanoGen for analysis {analysis_name}")
        
        script = os.path.join(
            tmgtools_path, 
            "main.py"
        )

        subprocess.run(
            [ 
                "python3", 
                script, 
                "--campaign",
                campaign,
                "--process",
                procname,
                "--mode", 
                "nanogen", 
            ] + (["--submit"] if submit else [])
        )

    logger.info("NanoGen execution completed.")
