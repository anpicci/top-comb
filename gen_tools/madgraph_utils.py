import re
import random
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from .utils import write_text
from typing import Dict, List, Any, Tuple
import numpy as np

from utils import (
    open_template, 
    create_dir,
    get_rwgt_name, 
    get_rwgt_points, 
    get_logger
)

# ============================================================
# Constants
# ============================================================
RESTRICT_CARD_INITIAL_VALUE = 0.1
RESTRICT_CARD_INCREMENT = 0.1
RESTRICT_CARD_AVOID_VALUE = 1.0
RANDOM_VALUE_MIN = -0.999999
RANDOM_VALUE_MAX = 0.999999
MIN_NONZERO_THRESHOLD = 1e-12
ZERO_THRESHOLD = 1e-9
DEFAULT_PRECISION = 0.000000

logger = get_logger(__name__)

# ============================================================
# MadGraph Card Preparation
# ============================================================
def prepare_proc_card( metadata: Dict[str, Any] ) -> None:
    """
    Create the proc_card specifying the process and output directory.
    """
    procname = metadata["name"]
    card_lines = [
        f"import model {metadata['model']}",
        "",
        *metadata["process"],
        "",
        f"output {procname} -nojpeg",
    ]
    card_content = "\n".join(card_lines)
    return card_content


def prepare_extramodels(metadata: Dict[str, Any]) -> None:
    """
    Write a file that tells MG which extra models to load.
    """
    return metadata["load_extramodels"]


def prepare_run_card(metadata: Dict[str, Any] ) -> None:
    """
    Render the run_card from a template specified in settings/metadata.
    """
    tpl = open_template(metadata["template_run_card"]["name"])
    return tpl

def prepare_restrict_card(
        metadata: Dict[str, Any],
        operators: List[Tuple[str, Any]],
    ) -> None:
    """
    Render the restrict card with operator values.
    If operator names are provided, this function updates the template to set
    small non-zero values for operator parameters so MG treats them as active.
    """
    tpl = open_template(metadata["template_restrict_card"]["name"])

    if operators:
        tpl = _update_restrict_card_operators(tpl, operators)

    return tpl


def _update_restrict_card_operators(template: str, operators: List[Tuple[str, Any]]) -> str:
    """
    Update restrict card template with non-zero operator values.
    """
    val = RESTRICT_CARD_INITIAL_VALUE
    
    for op in np.array(operators)[:, 0]:
        pattern = re.search(f"(.*{op}.*)", template)
        if not pattern:
            continue

        line = pattern.group(0)
        new_val = f"{val:3.6f}e-01"
        template = template.replace(line, line.replace("0.000000e+00", new_val))

        # Workaround: avoid exactly reaching 1.0 due to MG bug
        val += RESTRICT_CARD_INCREMENT
        if abs(val - RESTRICT_CARD_AVOID_VALUE) < ZERO_THRESHOLD:
            val += RESTRICT_CARD_INCREMENT
    
    return template


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

def prepare_customizecards(
        metadata: Dict[str, Any],
        operators: List[Tuple[str, Any]],
    ) -> None:
    """
    Create customizecards by appending EFT operator settings and extra opts.
    Randomized operator values are used here for initial configuration; callers
    may override these later if needed.
    """
    tpl = open_template(metadata["template_customizecards"]["name"])
    
    content_parts = [tpl]
    
    # Add EFT operators section
    if operators:
        content_parts.append(_generate_operator_settings(operators))
    
    # Add user settings section
    extra_opts = metadata["template_customizecards"]["extraopts"]
    if extra_opts:
        content_parts.append(_generate_user_settings(extra_opts))
    
    return "\n".join(content_parts)

def prepare_reweightcards(
        rwgt_points: List[np.ndarray],
    ) -> None:
    """
    Build reweight_card 
    """
    date_str = datetime.now().strftime("%A %d. %B %Y")
    
    lines = [
        f"# Reweight card created on {date_str}",
        "change rwgt_dir rwgt",
        "launch --rwgt_name=dummy",
        ""
    ]
    
    for point in rwgt_points:
        name = get_rwgt_name(point)
        lines.append(f"launch --rwgt_name={name}")
        for param, val in point:
            lines.append(f"set {param} {float(val):3.4f}")
        lines.append("")
    
    # Write reweight card
    return "\n".join(lines)

def _generate_reweight_points(operators: List[Tuple[str, Any]]) -> List[np.ndarray]:
    """
    Generate all reweighting points including SM point.
    """
    rwgt_points = get_rwgt_points(operators, 1)
    if len(operators) > 2:
        rwgt_points += get_rwgt_points(operators, 2)

    # Add SM point by cloning last point and zeroing couplings
    if rwgt_points:
        sm_point = deepcopy(rwgt_points[-1])
        sm_point[:, 1] = "0.0"
        rwgt_points.append(sm_point)
    
    return rwgt_points

def _build_reweight_readme(
        outdir: Path,
        rwgt_points: List[np.ndarray],
        operators: List[Tuple[str, Any]]
    ) -> str:

    """
    Build README.md content with reweight point mapping.
    """
    date_str = datetime.now().strftime("%A %d. %B %Y")
    operator_names = [op[0] for op in operators]

    lines = [
        f"# Configuration card created on {date_str}",
        "Below is a mapping showing the reweighting points found in NanoAOD.",
        f"The full list of couplings: {operator_names}",
        "",
        "| Coupling values | Index |",
        "| :-------------- | :-----|",
    ]

    for i, point in enumerate(rwgt_points):
        nonzero = [f"{p}={v}" for p, v in point if float(v) != 0]
        label = "SM" if not nonzero else ", ".join(nonzero)
        lines.append(f"| {label} | {i} |")

    with open( outdir / "README.md", "w") as f:
        f.write( "\n".join(lines) )

def _build_reweight_mapping(
        outdir: Path,
        rwgt_points: List[np.ndarray],
        operators: List[Tuple[str, Any]]
    ) -> str:

    """
    Build README.md content with reweight point mapping.
    """

    data = {} 

    for i, point in enumerate(rwgt_points):
        name = get_rwgt_name(point)
        nonzero = [f"{p}={v}" for p, v in point if float(v) != 0]
        label = "SM" if not nonzero else ", ".join(nonzero)
        #.append(f"| {label} | {i} |")
        data[ name ] = {
            "index": i,
            "all_couplings": { p: float(v) for p, v in point }
        }
    with open( outdir / "reweight_mapping.json", "w") as f:
        json.dump( data, f, indent=4 )
    
    return data 

def _generate_operator_settings(operators: List[Tuple[str, Any]]) -> str:
    """
    Generate operator parameter settings for customize card.
    """
    lines = ["\n\n# EFT operators"]
    for op in np.array(operators)[:, 0]:
        val = generate_random_operator_value()
        lines.append(f"set param_card {op} {val}")
    return "\n".join(lines)

def generate_random_operator_value() -> float:
    """
    Generate a random non-zero value for operator initialization.
    """
    val = random.uniform(RANDOM_VALUE_MIN, RANDOM_VALUE_MAX)
    while abs(val) < MIN_NONZERO_THRESHOLD:
        val = random.uniform(RANDOM_VALUE_MIN, RANDOM_VALUE_MAX)
    return val

def _generate_user_settings(extra_opts: List[str]) -> str:
    """
    Generate user settings section for customize card.
    """
    lines = ["\n\n# User settings"]
    lines.extend(extra_opts)
    return "\n".join(lines)

