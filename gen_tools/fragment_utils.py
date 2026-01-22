from pathlib import Path
from typing import Dict, Any, List
import re

from utils import (
    open_template, 
    get_logger
)

logger = get_logger(__name__)

def _prepare_fragment(
        gridpack_path: str,
        proc_metadata: Dict[str, Any],
    ) -> None:
    """
    Render the fragment.py used by the event production step.
    """

    procname = proc_metadata["name"]
    tpl = open_template(
        proc_metadata["fragment"]["name"]
    )

    param_text = _format_process_parameters(
        proc_metadata["fragment"]["process_parameters"],
        tpl
    )

    fragment_content = tpl.format(
        GRIDPACK=gridpack_path,
        PROCESS_PARAMETERS=param_text
    )

    return fragment_content


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

