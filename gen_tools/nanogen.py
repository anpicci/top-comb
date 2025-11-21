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
        tmgtools_path
    ):
    
    """
    Run NanoGen validation for each configured process using tmg-tools.
    """

    logger.info(f"Running NanoGen for analysis {analysis_name}")
    gen_metadata = load_config( 
        analysis_meta["generation"] 
    )

    samples = gen_metadata["samples"]
    for sample_metadata in samples:
        procname = sample_metadata["name"]
        
        outdir = os.path.join(
            workdir, 
            procname
        )

        script = os.path.join(
            tmgtools_path, 
            "main.py"
        )

        jsonfile = os.path.join(
            outdir, 
            "nanogen_config.json"
        )

        subprocess.run(
            [ 
                "python3", 
                script, 
                "--parse_from_json", 
                jsonfile, 
                "--mode", 
                "nanogen", 
                "--submit"
            ]
        )

    logger.info("NanoGen execution completed.")
