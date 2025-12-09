"""
Setup
---------------
Helpers to prepare MadGraph cards, fragments and submission scripts for
event generation workflows.
"""

import re
import json
import random
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import numpy as np

from utils import (
    load_config, open_template, get_operators, create_dir,
    get_rwgt_name, get_rwgt_points
)

def write_text(path: str, text: str):
    """Write text to file (small utility to keep code concise)."""
    with open(path, "w") as f:
        f.write(text)

# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------
def setup_gen_config(
        analysis_name, 
        analysis_meta, 
        workdir, 
        outpath,
        tmgtools_path,
        genprod_image,
        genprod_repo,
        genprod_branch
    ):

    """
    Create generation work directories and prepare MadGraph configuration.
    """
    # Load generation metadata
    gen_metadata = load_config(
        analysis_meta["generation"]
    )
    selected_operators = analysis_meta.get("operators")
    operators = get_operators( selected_operators )

    # Go over samples
    samples = gen_metadata["samples"]
    for proc_metadata in samples:
        procname = proc_metadata["name"]

        mgworkdir = Path(workdir) / procname
        mgcards_dir = mgworkdir / "mgcards"
        create_dir( 
            dirname = mgcards_dir 
        )

        # Write all MadGraph cards and related config fragments
        prepare_proc_card(
            metadata = proc_metadata, 
            mgworkdir = mgcards_dir
        )
        
        prepare_run_card(
            metadata = proc_metadata, 
            mgworkdir = mgcards_dir
        )
        
        prepare_extramodels(
            metadata = proc_metadata, 
            mgworkdir = mgcards_dir
        )
        
        prepare_customizecards(
            metadata = proc_metadata, 
            mgworkdir = mgcards_dir, 
            operators = operators
        )
        
        prepare_restrict_card(
            metadata = proc_metadata, 
            mgworkdir = mgcards_dir, 
            operators = operators
        )
        
        prepare_reweightcards(
            metadata = proc_metadata, 
            mgworkdir = mgcards_dir, 
            operators = operators
        )

        # Create the fragment used by the event production step
        prepare_fragment(
            analysis_name = analysis_name, 
            metadata = proc_metadata, 
            mgworkdir = mgworkdir, 
            outpath = outpath
        )

        # Prepare submission and gridpack helper scripts
        prepare_submission_nanogen_file(
            metadata = proc_metadata, 
            mgworkdir = mgworkdir, 
            tmgtools_path = tmgtools_path,
            outpath = f"{outpath}/{analysis_name}"
        )
        
        create_gridpack_submit(
            analysis_name = analysis_name, 
            metadata = proc_metadata, 
            outpath = outpath, 
            mgworkdir = mgworkdir, 
            genprod_image = genprod_image, 
            genprod_repo = genprod_repo, 
            genprod_branch = genprod_branch
        )


# ------------------------------------------------------------
# MadGraph cards
# ------------------------------------------------------------
def prepare_proc_card(metadata, mgworkdir):
    """
    Create the proc_card specifying the process and output directory.
    """
    procname = metadata["name"]
    full_card = [
        f"import model {metadata['model']}",
        "",
        *metadata["process"],
        "",
        f"output {procname} -nojpeg",
    ]

    write_text(mgworkdir / f"{procname}_proc_card.dat", "\n".join(full_card))


def prepare_extramodels(metadata, mgworkdir):
    """
    Write a file that tells MG which extra models to load.
    """
    procname = metadata["name"]
    write_text(mgworkdir / f"{procname}_extramodels.dat", metadata["load_extramodels"])


def prepare_run_card( metadata, mgworkdir ):
    """
    Render the run_card from a template specified in settings/metadata.
    """
    procname = metadata["name"]
    tpl = open_template( metadata["template_run_card"]["name"] )
    write_text(mgworkdir / f"{procname}_run_card.dat", tpl)


def prepare_restrict_card(metadata, mgworkdir, operators):
    """
    Render the restrict card.

    If operator names are provided, this function updates the template to set
    small non-zero values for operator parameters so MG treats them as active.
    """
    procname = metadata["name"]
    tpl = open_template( metadata["template_restrict_card"]["name"] )

    if operators:
        # Set small non-zero defaults for each operator to avoid MG ignoring them
        val = 0.1
        for op in np.array(operators)[:, 0]:
            pattern = re.search(f"(.*{op}.*)", tpl)
            if not pattern:
                continue

            line = pattern.group(0)
            new_val = f"{val:3.6f}e-01"
            tpl = tpl.replace(line, line.replace("0.000000e+00", new_val))

            # Workaround: avoid exactly reaching 1.0 due to MG bug
            val += 0.1
            if abs(val - 1.0) < 1e-9:
                val += 0.1

    restrict_name = metadata["template_restrict_card"]["restrict_name"]
    write_text(mgworkdir / f"{procname}_restrict_{restrict_name}.dat", tpl)


def prepare_customizecards(metadata, mgworkdir, operators):
    """
    Create customizecards by appending EFT operator settings and any extra opts.

    Randomized operator values are used here for initial configuration; callers
    may override these later if needed.
    """
    procname = metadata["name"]
    tpl = open_template( metadata["template_customizecards"]["name"] )

    tpl += "\n\n# EFT operators\n"

    if operators:
        for op in np.array(operators)[:, 0]:
            # Use a random non-zero value in (-1, 1)
            val = random.uniform(-0.999999, 0.999999)
            if abs(val) < 1e-12:  # ensure non-zero
                val = random.uniform(-0.999999, 0.999999)
            tpl += f"set param_card {op} {val}\n"

    extra_opts = metadata["template_customizecards"]["extraopts"]
    if extra_opts:
        tpl += "\n\n# User settings\n"
        tpl += "\n".join(extra_opts)

    write_text(mgworkdir / f"{procname}_customizecards.dat", tpl)


def prepare_reweightcards(metadata, mgworkdir, operators):
    """
    Build a reweight_card that contains all reweighting points used for
    systematic/envelope studies. It also produces README.md in the parent 
    directory with a human-readable mapping of the reweight points to 
    indices.
    """
    procname = metadata["name"]

    date_str = datetime.now().strftime("%A %d. %B %Y")

    header = (
        f"# Reweight card created on {date_str}\n"
        "change rwgt_dir rwgt\n"
        "launch --rwgt_name=dummy\n\n"
    )

    if len(operators) == 0:
        return
    
    rwgt_points = get_rwgt_points(operators, 1)
    if len(operators) > 2:
        rwgt_points += get_rwgt_points(operators, 2)

    # Add SM point by cloning last point and zeroing couplings
    if rwgt_points:
        sm = deepcopy(rwgt_points[-1])
        sm[:, 1] = "0.0"
        rwgt_points.append(sm)

    text = header
    for point in rwgt_points:
        name = get_rwgt_name(point)
        text += f"launch --rwgt_name={name}\n"
        for param, val in point:
            text += f"set {param} {float(val):3.4f}\n"
        text += "\n"

    write_text(mgworkdir / f"{procname}_reweight_card.dat", text)

    # Markdown summary for quick reference
    operator_names = [op[0] for op in operators]

    md_lines = [
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
        md_lines.append(f"| {label} | {i} |")

    write_text(mgworkdir.parent / "README.md", "\n".join(md_lines))


# ------------------------------------------------------------
# Fragment / submission
# ------------------------------------------------------------
def prepare_fragment(analysis_name, metadata, mgworkdir, outpath):
    """
    Render the fragment.py used by the event production step.
    """

    procname = metadata["name"]
    tpl = open_template( metadata["fragment"]["name"] )

    gridpacks_base = f"{outpath}/{analysis_name}/{procname}"

    # Remove any redirectors from the fragment path
    gridpacks_base = gridpacks_base.replace("root://eosuser.cern.ch//", "") 
    gridpack_path = f"{gridpacks_base}/gridpack/{procname}.tar.xz"

    params = ["# Process specific settings"] + metadata["fragment"]["process_parameters"]

    # Preserve indentation when inserting a multi-line parameter list
    placeholder = re.search(r"^(?P<indent>\s*)\{PROCESS_PARAMETERS\}", tpl, flags=re.MULTILINE)
    indent = placeholder.group("indent") if placeholder else ""
    param_text = (",\n" + indent).join(params)

    tpl = tpl.format(GRIDPACK=gridpack_path, PROCESS_PARAMETERS=param_text)
    write_text(mgworkdir / "fragment.py", tpl)


def prepare_submission_nanogen_file(
        metadata, 
        mgworkdir, 
        outpath,
        tmgtools_path,
    ):
    """
    Create a small JSON config used to submit nanogen validation jobs.
    """

    procname = metadata["name"]
    data = {
        "samples": [
            {
            "outpath" : outpath,
            "name" : procname,
            "fragment": f"file:{mgworkdir}/fragment.py",
            "nevents":  1e5,
            "memory": 32000,
            "njobs": 200,
            "xsec": 1,
            "isGS": 0
            }
        ]
    }

    outpath = Path(f"{tmgtools_path}/processes/{metadata['name']}")
    create_dir( outpath )
    write_text( tmgtools_path / outpath / "job.json", json.dumps(data, indent=4) )


def create_gridpack_submit(
        analysis_name, 
        metadata, 
        outpath, 
        mgworkdir,
        genprod_image,
        genprod_repo,
        genprod_branch
    ):
    """
    Create helper scripts to run the gridpack creation and submission.
    """
    procname = metadata["name"]

    # Render bash wrapper from the provided template
    bash_tpl = open_template(
        "templates/run_gridpack_batch.sh"
    )

    subs = {
        "__PROCNAME__": procname,
        "__ANALYSIS_NAME__": analysis_name,
        "__CARDSDIR__": "mgcards",
        "__SINGULARITY_IMAGE__": genprod_image,
        "__GENPRODUCTIONS_GRIDPACK__": genprod_repo,
        "__BRANCH_GRIDPACK__": genprod_branch,
    }

    for k, v in subs.items():
        bash_tpl = bash_tpl.replace(k, v)

    write_text(mgworkdir / "run_gridpack_batch.sh", bash_tpl)

    # Render condor submission description file
    jds_tpl = open_template(
        "templates/template_submit.jds"
    )

    jds_subs = {
        "__SCRIPTNAME__": "run_gridpack_batch.sh",
        "__OUTPATH__": f"{outpath}/{analysis_name}/{procname}/gridpack",
        "__PROCNAME__": f"{procname}_runGridpack",
        "__NCORES__": "8",
    }

    for k, v in jds_subs.items():
        jds_tpl = jds_tpl.replace(k, v)

    write_text(mgworkdir / "run_gridpack_batch.jds", jds_tpl)

