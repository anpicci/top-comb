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

from settings import TopCombSettings
settings = TopCombSettings().model_dump()
outpath = settings["topcomb_outpath"]

def write_text(path: str, text: str):
    """Write text to file (small utility to keep code concise)."""
    with open(path, "w") as f:
        f.write(text)

# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------
def setup_gen_config(analysis_name, analysis_meta, workdir, settings):
    """
    Create generation work directories and prepare MadGraph configuration.
    """
    # Load generation metadata
    gen_metadata = load_config(analysis_meta["generation"])
    samples = gen_metadata["samples"]
    selected_operators = analysis_meta["operators"]

    samples = gen_metadata["samples"]
    operators = get_operators( selected_operators )

    for proc_gen_metadata in samples:
        procname = proc_gen_metadata["name"]

        outdir = Path(workdir) / procname
        mgcards_dir = outdir / "mgcards"
        create_dir(mgcards_dir)

        proc_metadata = { **settings, **proc_gen_metadata }

        # Write all MadGraph cards and related config fragments
        prepare_proc_card(proc_metadata, mgcards_dir)
        prepare_run_card(proc_metadata, proc_gen_metadata, mgcards_dir)
        prepare_extramodels(proc_metadata, mgcards_dir)
        prepare_customizecards(proc_metadata, mgcards_dir, operators)
        prepare_restrict_card(proc_metadata, mgcards_dir, operators)
        prepare_reweightcards(proc_metadata, mgcards_dir, operators)

        # Create the fragment used by the event production step
        prepare_fragment(analysis_name, proc_gen_metadata, outdir)

        # Prepare submission and gridpack helper scripts
        prepare_submission_nanogen_file(analysis_name, gen_metadata, procname, outdir)
        create_gridpack_submit(analysis_name, settings, proc_gen_metadata, outdir)


# ------------------------------------------------------------
# MadGraph cards
# ------------------------------------------------------------
def prepare_proc_card(metadata, outdir):
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

    write_text(outdir / f"{procname}_proc_card.dat", "\n".join(full_card))


def prepare_extramodels(metadata, outdir):
    """
    Write a file that tells MG which extra models to load.
    """
    procname = metadata["name"]
    write_text(outdir / f"{procname}_extramodels.dat", metadata["load_extramodels"])


def prepare_run_card(settings, metadata, outdir):
    """
    Render the run_card from a template specified in settings/metadata.
    """
    procname = metadata["name"]
    tpl = open_template( metadata["template_run_card"]["name"] )
    write_text(outdir / f"{procname}_run_card.dat", tpl)


def prepare_restrict_card(metadata, outdir, operators):
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
    write_text(outdir / f"{procname}_restrict_{restrict_name}.dat", tpl)


def prepare_customizecards(metadata, outdir, operators):
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

    write_text(outdir / f"{procname}_customizecards.dat", tpl)


def prepare_reweightcards(metadata, outdir, operators):
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

    rwgt_points = get_rwgt_points(operators, 1)
    if len(operators) >= 2:
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

    write_text(outdir / f"{procname}_reweight_card.dat", text)

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

    write_text(outdir.parent / "README.md", "\n".join(md_lines))


# ------------------------------------------------------------
# Fragment / submission
# ------------------------------------------------------------
def prepare_fragment(analysis_name, metadata, outdir):
    """
    Render the fragment.py used by the event production step.
    """

    procname = metadata["name"]
    tpl = open_template( metadata["fragment"]["name"] )

    gridpacks_base = Path(outpath) / analysis_name / procname
    gridpack_path = gridpacks_base / "gridpack" / f"{procname}.tar.xz"

    params = ["# Process specific settings"] + metadata["fragment"]["process_parameters"]

    # Preserve indentation when inserting a multi-line parameter list
    placeholder = re.search(r"^(?P<indent>\s*)\{PROCESS_PARAMETERS\}", tpl, flags=re.MULTILINE)
    indent = placeholder.group("indent") if placeholder else ""
    param_text = (",\n" + indent).join(params)

    tpl = tpl.format(GRIDPACK=gridpack_path, PROCESS_PARAMETERS=param_text)
    write_text(outdir / "fragment.py", tpl)


def prepare_submission_nanogen_file(analysis_name, metadata, procname, outdir):
    """
    Create a small JSON config used to submit nanogen validation jobs.
    """


    data = {
        "producer" : {
            "mode": "nanogen",
            "tag": f"submit_nanogen_{procname}"
        },
        "settings": {
            "outpath": f"{outpath}/{analysis_name}/{procname}/nanogen",
            "campaign": "RunIISummer20UL18",
        },
        "samples": [
            {
            "name" : procname,
            "fragment": f"file:{outdir}/fragment.py",
            "nevents":  1e6,
            "memory": 32000,
            "njobs": 5000,
            "xsec": 1,
            "isGS": 0
            }
        ]
    }

    write_text(outdir / "nanogen_config.json", json.dumps(data, indent=4))


def create_gridpack_submit(analysis_name, settings, metadata, outdir):
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
        "__OUTPATH__": outpath,
        "__SINGULARITY_IMAGE__": settings["singularity_image_gridpack"],
        "__GENPRODUCTIONS_GRIDPACK__": settings["genproductions_gridpack"],
        "__BRANCH_GRIDPACK__": settings["branch_gridpack"],
    }

    for k, v in subs.items():
        bash_tpl = bash_tpl.replace(k, v)

    write_text(outdir / "run_gridpack_batch.sh", bash_tpl)

    # Render condor submission description file
    jds_tpl = open_template(
        "templates/template_submit.jds"
    )

    jds_subs = {
        "__SCRIPTNAME__": "run_gridpack_batch.sh",
        "__PROCNAME__": f"{procname}_runGridpack",
        "__NCORES__": "8",
    }

    for k, v in jds_subs.items():
        jds_tpl = jds_tpl.replace(k, v)

    write_text(outdir / "run_gridpack_batch.jds", jds_tpl)

