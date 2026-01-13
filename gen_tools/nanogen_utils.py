from .utils import write_text
from pathlib import Path
from typing import Dict, Any, List
import re
from .generation_config import GenerationConfig

from utils import (
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
    mgworkdir = config.workdir / "processes" / procname
    
    config_data = {
        "gen": [
            {
                "name": procname,
                "config": f"file:{mgworkdir}/fragment.py",
                "xsec": 1,
                "isGS": 0
            }
        ]
    }

    config_dir = Path(f"{config.mcprod_path}/processes/{procname}")
    create_dir(config_dir)
    write_text(config_dir / "job.json", json.dumps(config_data, indent=4))