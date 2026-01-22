from .utils import write_text
from pathlib import Path
from typing import Dict, Any, List
import re

from utils import (
    create_dir
)

import json

def _prepare_nanogen(
        procdir:str ,
        mcprod_path: str,
        proc_metadata: Dict[str, Any],
    ) -> None:
    """
    Create a JSON config used to submit nanogen validation jobs with TMG-tools.
    """
    procname = proc_metadata["name"]
    
    config_data = {
        "gen": [
            {
                "name": procname,
                "config": f"file:{procdir}/fragment.py",
                "xsec": 1,
                "isGS": 0
            }
        ]
    }

    config_dir = Path(f"{mcprod_path}/processes/{procname}")
    create_dir(config_dir)
    write_text(config_dir / "job.json", json.dumps(config_data, indent=4))