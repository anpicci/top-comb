from .utils import write_text
from pathlib import Path
from typing import Dict, Any, List
import re
from .generation_config import GenerationConfig

from utils import (
    open_template, 
    get_logger
)

logger = get_logger(__name__)

def _prepare_fragment(
        proc_metadata: Dict[str, Any],
        config: GenerationConfig
    ) -> None:
    """
    Render the fragment.py used by the event production step.
    """

    procname = proc_metadata["name"]
    mgworkdir = config.workdir / "processes" / procname
    tpl = open_template(
        proc_metadata["fragment"]["name"]
    )

    gridpack_path = _get_gridpack_path(config.outpath, config.measurement_name, procname)
    param_text = _format_process_parameters(
        proc_metadata["fragment"]["process_parameters"],
        tpl
    )

    fragment_content = tpl.format(
        GRIDPACK=gridpack_path,
        PROCESS_PARAMETERS=param_text
    )

    write_text(Path(mgworkdir) / "fragment.py", fragment_content)

def _format_process_parameters(parameters: List[str], template: str) -> str:
    """
    Format process parameters preserving template indentation.
    """

    params = ["# Process specific settings"] + parameters
    
    # Preserve indentation when inserting a multi-line parameter list
    placeholder = re.search(
        r"^(?P<indent>\s*)\{PROCESS_PARAMETERS\}",
        template,
        flags=re.MULTILINE
    )
    indent = placeholder.group("indent") if placeholder else ""
    
    return (",\n" + indent).join(params)

def _get_gridpack_path(
        outpath: str,
        measurement_name: str,
        procname: str
    ) -> str:
    """
    Construct gridpack path with redirector removed.
    """
    gridpacks_base = f"{outpath}/{measurement_name}/{procname}"
    # Remove any redirectors from the fragment path
    gridpacks_base = gridpacks_base.replace("root://eosuser.cern.ch/", "")
    return f"{gridpacks_base}/gridpack/gridpack.tar.xz"

