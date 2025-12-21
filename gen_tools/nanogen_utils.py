from .utils import write_text
from pathlib import Path
from typing import Dict, Any, List
import re
from .generation_config import GenerationConfig

from utils import (
    open_template, 
    get_logger,
    create_dir
)

import json

def _prepare_nanogen(
        proc_metadata: Dict[str, Any],
        config: GenerationConfig
    ) -> None:
    """
    Create a JSON config used to submit nanogen validation jobs with TMG-tools.
    """
    procname = proc_metadata["name"]
    mgworkdir = config.workdir / procname
    
    config_data = {
        "samples": [
            {
                "outpath": config.outpath,
                "name": procname,
                "fragment": f"file:{mgworkdir}/fragment.py",
                "nevents": 1e6,
                "memory": 32000,
                "njobs": 5000,
                "xsec": 1,
                "isGS": 0
            }
        ]
    }

    config_dir = Path(f"{config.tmgtools_path}/processes/{procname}")
    create_dir(config_dir)
    write_text(config_dir / "job.json", json.dumps(config_data, indent=4))