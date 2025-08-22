"""
This macro takes a config yml file and writes a reweight card based on the information.
"""
import os
import re
import json
import argparse
import textwrap
import numpy as np
from datetime import datetime
import utils.auxiliars as aux
from copy import deepcopy

# Create the logger instance
from utils.logger import get_logger
logger = get_logger( __name__ )

def open_template(template_path):
    """Read and return the content of a template file """
    main_path = os.environ["TOPCOMB_MAINPATH"]
    with open(os.path.join(main_path, template_path)) as f:
        return f.read()


def create_main_parser():
    """Create and return the main argument parser."""
    parser = argparse.ArgumentParser(
        description="Functionalities to setup a new analysis for the combination."
    )

    parser.add_argument(
        "--config",
        dest="config",
        default="configs/TTG_TOP-23-002.yml",
        type=str,
        help="Path to config file"
    )

    return parser.parse_args()


def write_text(outfile, text):
    """Write text to a file."""
    with open(outfile, "w") as out:
        out.write(text)


def write_proc_card(outdir, meta):
    """Write the process card from the metadata."""
    procname = meta['procname']
    full_card = [
        f"import model {meta['model']}",
        "",
        *meta['process'],
        "",
        f"output {procname} -nojpeg"
    ]
    write_text(os.path.join(outdir, f"{procname}_proc_card.dat"), "\n".join(full_card))

def write_extramodels(outdir, meta):
    """Write the extramodels card as default."""
    modelname = meta['load_extramodels'] 
    write_text(os.path.join(outdir, f"{procname}_extramodels.dat"), modelname)

def write_run_card(outdir, meta):
    """Write the run card from the metadata (pass-through from template)."""
    procname = meta['procname']
    template_name = meta['template_run_card']['name']
    text = open_template(template_name)
    write_text(os.path.join(outdir, f"{procname}_run_card.dat"), text)

def write_restrict_card(outdir, meta, operators):
    """Write the customizecards file from the metadata."""
    procname = meta['procname']
    template = meta['template_restrict_card']['name']
    text = open_template(template)
    write_text(os.path.join(outdir, f"{procname}_{outname}.dat"), "\n".join(newtext))

def write_customizecards(outdir, meta, operators):
    """Write the customizecards file from the metadata."""
    procname = meta['procname']
    template_name = meta['template_customizecards']['name']
    extra_opts = meta['template_customizecards']['extraopts']

    text = open_template(template_name)

    # EFT operators
    text += "\n\n# EFT operators\n"
    for op, ref in np.array(operators)[:, 0:2]:
        text += f"set param_card DIM6 {op} {ref}\n"

    # Extra user settings
    text += "\n\n# User settings"
    for opt in extra_opts:
        text += f"\n{opt}"

    write_text(os.path.join(outdir, f"{procname}_customizecards.dat"), text)


def write_reweightcards(outdir, procname, operators, algorithm):
    """Write the reweight card based on operators and algorithm for combining operators."""
    text = f"# Reweight card created on {datetime.now().strftime('%A %d. %B %Y')}\n"
    text += "change rwgt_dir rwgt\n"
    text += "launch --rwgt_name=dummy # Name of first argument seems to be rwgt_1. Add dummy to fix it.\n\n"

    rwgt_points = []
    for algo in algorithm.split("-"):
        rwgt_points += aux.get_rwgt_points(algo, operators)

    # Add the SM point
    sm = deepcopy( rwgt_points[-1] )
    sm[:, 1] = "0.0"
    rwgt_points.append( sm )
    for rwgt_point in rwgt_points:
        rwgt_name = aux.get_rwgt_name(rwgt_point)
        text += f"launch --rwgt_name={rwgt_name}\n"
        for param, value in rwgt_point:
            text += f"set {param} {float(value):3.4f}\n"
        text += "\n"

    write_text(os.path.join(outdir, f"{procname}_reweight_card.dat"), text)

    # Also write a markdown table with the coupling mappings

    mdtext = f"# Configuration card created on {datetime.now().strftime('%A %d. %B %Y')}\n"
    mdtext += "Below there is a mapping showing the reweighting points that can be found in the NanoAOD. " 
    mdtext += "Note that we only add to the first columns the couplings that are not set to 0!" 

    operator_names = [ op[0] for op in operators ]  
    mdtext += f"The full list of couplings considered for this version is: {operator_names}.\n" 

    mdtext += "| Coupling values | Index in LHEReweightWeight |\n" 
    mdtext += "| :-------- | :-------- |\n" 
    for irwgt, rwgt_point in enumerate(rwgt_points):
        values = []
        for param, value in  rwgt_point:
            if float(value) != 0.0:
                values.append( f"{param}={value}" )
        
        if values == []:
            # this is the sm
            line = "SM"
        else:
            line = ",".join( values )

        mdtext += f"| {line} | {irwgt} |\n"

    mddir = outdir.replace("mgcards", "")
    write_text(os.path.join( mddir, f"{procname}_reweighting_maps.md"), mdtext)


def write_fragment(outdir, meta):
    """Modify a PS template and save it to the analysis folder."""
    procname = meta['procname']
    fragment_meta = meta['fragment']

    text = open_template(fragment_meta['name'])

    topcomb_gridpacks = os.path.join(os.environ['TOPCOMB_OUTPATH'], f"top-comb/{procname}")
    gridpack_path = f"{topcomb_gridpacks}/gridpack/{procname}.tar.xz"

    process_params = ['# Process specific settings'] + fragment_meta['process_parameters']

    # Find indentation for {PROCESS_PARAMETERS}
    placeholder_match = re.search(r'^(?P<indent>\s*)\{PROCESS_PARAMETERS\}', text, flags=re.MULTILINE)
    indent = placeholder_match.group('indent') if placeholder_match else ''

    formatted_params = (",\n" + indent).join(process_params)

    text = text.format(
        GRIDPACK=gridpack_path,
        PROCESS_PARAMETERS=formatted_params
    )

    write_text(os.path.join(outdir, "fragment.py"), text)


def write_submission_nanogen_file(outdir, meta):
    """Write a configuration file to be used with tmg-tools/top-gendqm."""
    procname = meta['procname']

    data = {
        "mode": "nanogen",
        "processes": {procname: f"file:{outdir}/fragment.py"},
        "nevents": {procname: 1e6},
        "memory": {procname: 32000},
        "njobs": {procname: 1000},
        "xsec": {procname: 1},
        "isGS": {procname: 0},
        "campaign": "RunIISummer20UL18",
        "outpath": os.path.join(os.environ['TOPCOMB_OUTPATH'], "top-comb/nanogen/"),
        "submit_dir": f"submit_nanogen_{procname}",
        "tag": procname,
        "routines": []
    }
    with open(os.path.join(outdir, "nanogen_config.json"), "w") as outfile:
        json.dump(data, outfile, indent=4)


if __name__ == "__main__":
    # ---- Implement here the main logic
    args = create_main_parser()
    
    # Load configurations
    metadata = aux.load_config(args.config)
    analysis_name = metadata['analysis_name']
    
    logger.info(f"Creating directories for analysis: {analysis_name} ({args.config})")
    outdir = os.path.join(os.environ["TOPCOMB_INPUTS"], analysis_name)
    os.makedirs(outdir, exist_ok=True)
    
    operators = metadata['operators']['scans']
    algorithm = metadata['operators']['algo']
    
    if metadata['samples']:
        for sample_meta in metadata['samples']:
            procname = sample_meta['procname']
            proc_dir = os.path.join(outdir, procname)
            mgcards_dir = os.path.join(proc_dir, "mgcards")
            os.makedirs(mgcards_dir, exist_ok=True)
    
            # Matrix element configuration
            write_proc_card(mgcards_dir, sample_meta)
            write_extramodels(mgcards_dir, sample_meta)
            write_run_card(mgcards_dir, sample_meta)
            write_restrict_card(mgcards_dir, sample_meta, operators)
            write_customizecards(mgcards_dir, sample_meta, operators)
            write_reweightcards(mgcards_dir, procname, operators, algorithm)
    
            # Parton shower configuration
            write_fragment(proc_dir, sample_meta)
    
            # Nanogen submission configuration
            write_submission_nanogen_file(proc_dir, sample_meta)
    
