"""
This macro takes a config yml file and writes a reweight card based on the information.
"""
import re
import itertools
import textwrap 
import numpy as np
import yaml
import argparse
import os
import json
from datetime import datetime

def load_config( config_path ) -> dict:
    """ Loads a configuration file written in yml format """
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def open_template( template ):
    with open( os.environ["TOPCOMB_ANALYSES"] + f"/{template}" ) as openfile:
        return openfile.read()

def create_main_parser():
    # Define the main parser
    parser = argparse.ArgumentParser(
            description=(
                "Functionalities to setup a new analysis for the combination."
            ),
    )

    parser.add_argument(
            "--config", 
            dest = "config",
            default = "configs/TTG_TOP-23-002.yml",
            type = str, 
            help = "Path to config file"
    )

    return parser.parse_args()


def write_text( outfile, text ):
    with open(outfile, "w") as out:
        out.write( text )
    return

def write_proc_card( outdir, meta ):
    """ Writes the process card from the metadata """

    # Model content
    full_card = [ 
            f"import model {meta['model']}", 
            " " # space
    ]

    # Process content
    full_card += meta['process']

    # Output content
    full_card += [
            " ", # space 
            f"output {meta['procname']} -nojpeg" 
    ]

    text = "\n".join( full_card )

    write_text( f"{outdir}/{meta['procname']}_proc_card.dat", text )
    return

def write_run_card( outdir, meta ):
    """ Writes the process card from the metadata """
    text = open_template( meta['template_run_card']['name'] )

    # At the moment this is just a pass-through of the template run_card. 
    # We leave it like this in case developments are needed in the future.
    write_text( f"{outdir}/{meta['procname']}_run_card.dat", text )
    return

def write_customizecards( outdir, meta, all_operators ):
    """ Writes the process card from the metadata """

    text = open_template( meta['template_customizecards']['name'] )

    # Set the operators to a nonzero value so that MG knows they
    # have to be used.
    
    arr = np.array( all_operators )[:, 0:2]
    text += "\n\n# EFT operators"
    for op, ref in arr:
        text += f"set param_card {op} {ref}\n"


    text += "\n\n# User settings"
    for opt in meta['template_customizecards']['extraopts']:
        text += f"\n{opt}"


    # At the moment this is just a pass-through of the template run_card. 
    # We leave it like this in case developments are needed in the future.
    write_text( f"{outdir}/{meta['procname']}_customizecards.dat", text )
    return

def get_rwgt_blocks(algo, all_operators):
    """ Function to get reweighting points """
    print( f" >> Making groups of {algo}" )
    rwgt_block = ""

    r_pars = {
        "one_by_one" : 1,
        "two_by_two" : 2,
        "three_by_three" : 3
    }

    # --------------------
    # First of all, unroll the relevant information
    # This converts:
    # - (
    #     ['ctG', 1.0, -1.0, 1.0], 
    #     ['ctW', 1.0, -1.0, 1.0] 
    # )
    # into:
    # - [
    #    ('ctG', -1.0), 
    #    ('ctG', 1.0), 
    #    ('ctW', -1.0), 
    #    ('ctW', 1.0)
    # ]
    # Note: purposefully ignoring the reference 
    # point value and using only bound 

    unroll_operators = [ 
        (op[0], opbound) for op in all_operators  for opbound in op[2:] 
    ]

    # Now make all combinations, replacing N operators by 0
    operator_combinations = itertools.combinations( unroll_operators, r_pars[ algo ] )
    for comb in operator_combinations:

        # easier to work with arrays
        op_arr = np.array(comb)

        # Prune cases in which the same operator gets modified twice
        unique_names = list( set(op_arr[:, 0]) )
        if len(unique_names) != len(op_arr[:, 0]):
            continue

        # Generate a matrix with a size equal to the number of operators
        # that will be modified.

        # This is the information for the operators that are turned ON
        full_matrix = np.full( (len(all_operators), 2), '0', dtype = 'object' )
        full_matrix[:len(unique_names), :] = op_arr 

        # Fill with those that are turned OFF
        unused_operators = np.array(
                [ (op[0], '0.0') for op in all_operators if op[0] not in unique_names ]
        )
        full_matrix[len(unique_names):, :] = unused_operators


        # A bit of OCD but let's sort the full matrix by operator name
        full_matrix = full_matrix[full_matrix[:, 0].argsort()]

        # Set up a name
        rwgt_name = "_".join( 
                "{0}{1}".format( opname, opval.replace(".", "p").replace("-","minus") ) for opname, opval in full_matrix 
        )
        
        rwgt_block += f"launch --rwgt_name={rwgt_name}\n"
        for row in full_matrix:
            rwgt_block += f"set {row[0]} {float(row[1]):3.4f}\n"
        rwgt_block += "\n"
            

    return rwgt_block 


def write_reweightcards( outdir, meta, operators ):
    """ Writes the process card from the metadata """

    text = "# Reweight card created on " + datetime.now().strftime("%A %d. %B %Y") + "\n"
    text += "change rwgt_dir rwgt\n"
    text += "launch --rwgt_name=dummy # Name of first argument seems to be rwgt_1. Add dummy to fix it.\n\n"

    algorithm = meta['template_reweight_card']['algo']
    algos = algorithm.split("-")

    # Prepare reweighting points
    for algo in algos:
        text += get_rwgt_blocks(algo, operators)

    write_text( f"{outdir}/{meta['procname']}_reweight_card.dat", text )
    return

def write_fragment( outdir, meta ):
    """ Modify a PS template and add it to the analysis folder """

    text = open_template( meta['fragment']['name'] )

    # The name of the gridpack is fixed by the process settings
    topcomb_gridpacks = os.environ['TOPCOMB_OUTPATH'] + f"top-comb/{meta['procname']}"
    GRIDPACK = f"{topcomb_gridpacks}/gridpack_{meta['procname']}.tar.xz"

    # Now read the process settings
    PROCESS_PARAMETERS = ['# Process specific settings'] + meta['fragment']['process_parameters']


    # Find indentation of the {PROCESS_PARAMETERS} placeholder in the template
    placeholder_match = re.search(r'^(?P<indent>\s*)\{PROCESS_PARAMETERS\}', text, flags=re.MULTILINE)
    indent = placeholder_match.group('indent') if placeholder_match else ''

    # Format the parameters with proper indentation
    formatted_params = (",\n" + indent).join(PROCESS_PARAMETERS)  

    # Now substitute everything
    text = text.format( 
        GRIDPACK = GRIDPACK, 
        PROCESS_PARAMETERS = formatted_params
    )

    # And save the fragment
    write_text( f"{outdir}/fragment.py", text )


def write_submission_nanogen_file( outdir, meta ):
    """ Write a configuration file to be used with tmg-tools/top-gendqm """

    # Many fields are just filled with template numbers, just change
    # whenever you need either more or less events, etc...
    data = {
        "mode"       : "nanogen",
        "processes"  : { sample_meta['procname'] : f"file:{outdir}/fragment.py" },
        "nevents"    : { sample_meta['procname'] : 1e6 },        
        "memory"     : { sample_meta['procname'] : 32000 },        
        "njobs"      : { sample_meta['procname'] : 1000 },        
        "xsec"       : { sample_meta['procname'] : 1 },        
        "isGS"       : { sample_meta['procname'] : 0 },
        "campaign"   : "RunIISummer20UL18",
        "outpath"    : os.environ['TOPCOMB_OUTPATH'] + f"top-comb/nanogen/",
        "submit_dir" : f"submit_nanogen_{meta['procname']}",        
        "tag"        : meta['procname'],
        "routines"   : []
    }   

    with open( f"{outdir}/nanogen_config.json", "w" ) as outfile:
        json.dump( data, outfile, indent = 4 )


if __name__ == "__main__":
    parser = create_main_parser()

    # Load configurations
    metadata = load_config(parser.config)

    # Setup analysis directories
    analysis_name = metadata['analysis_name']

    print(f">> Creating directories for analysis: {analysis_name} ({parser.config})")
    outdir = os.path.join(os.environ["TOPCOMB_ANALYSES"], analysis_name)
    os.makedirs(outdir, exist_ok=True)

    # Write MadGraph cards if samples exist
    if metadata['samples']:


        for sample_meta in metadata['samples']:

            procname = sample_meta['procname']
            mgcards_dir = os.path.join(outdir, procname, "mgcards")
            os.makedirs(mgcards_dir, exist_ok=True)

            # Matrix element configuration
            write_proc_card(mgcards_dir, sample_meta)
            write_run_card(mgcards_dir, sample_meta)
            write_customizecards(mgcards_dir, sample_meta, metadata['operators'])
            write_reweightcards(mgcards_dir, sample_meta, metadata['operators'])

            # Parton shower configuration
            write_fragment(os.path.join(outdir, procname), sample_meta)

            # Prepare configuration file for generating nanogen  
            write_submission_nanogen_file(os.path.join(outdir, procname), sample_meta)  
