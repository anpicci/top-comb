# A set of functions that are useful
import sys
import yaml
import itertools
import numpy as np
import os
from datetime import datetime
import subprocess
import shutil

# Create the logger instance
from utils.logger import get_logger
logger = get_logger( __name__ )


from environment import TopCombEnv
settings = TopCombEnv().model_dump()
main_path = settings.get("mainpath")

def load_config( config_path ) -> dict:
    """ Loads a configuration file written in yml format """
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def prepare_workdir( environment ):
    """
    Setup the main folder: requires clean workdir
    """
    workdir = environment.get("workdir")
    reset = environment.get("reset")
    
    if os.path.exists(workdir):
        if reset:
            logger.info(f"Resetting existing workdir: {workdir}")
            shutil.rmtree(workdir)
        else:
            logger.error(
                f"Workdir already exists: {workdir}\n"
                f"Use --reset to regenerate setup."
            )
            sys.exit(1)
    create_dir(workdir)
    create_workdir_info_file(workdir)
    logger.debug(f"Workdir prepared fresh for setup_gen: {workdir}")
    return

def create_workdir_info_file(workdir: str):
    """Create a .txt file stating when the work directory was created."""
    # Format date: DD month YYYY
    date_str = datetime.now().strftime("%d %B %Y")
    message = f"This work directory was created on {date_str}"

    # Write file inside workdir
    file_path = os.path.join(workdir, "workdir_info.txt")
    with open(file_path, "w") as f:
        f.write(message)
    return file_path

def open_template( template_file ):
    """Read and return the content of a template file """
    with open(
            os.path.join(main_path, template_file)
        ) as f:
        return f.read()

def create_dir( dirname ):
    if not os.path.exists( dirname ):
        logger.info( f"Creating new work directory: {dirname}" )
        os.makedirs( dirname, exist_ok = True )

def copy_file( file, dest_dir = "." ):
    try:
        subprocess.run( ["cp", file, dest_dir] )
    except subprocess.CalledProcessError as e:
        logger.error( f"Error while copying file {file}. Exception: {e}" )

def get_operators( selected_operators ):
    """ Load info from metadata and return the list of operators """
    operators_file = "configs/list_operators.yml"
    operators = []
    opmeta = load_config( operators_file )
    for _, group_meta in opmeta.items():
        for op in group_meta:
            if op[0] in selected_operators:
                operators.append( op )
    return operators
         

def get_rwgt_points(all_operators, comb_scheme = 1):
    """ Function to get reweighting points """
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
        (op[0], opbound) for op in all_operators  for opbound in op[1:] 
    ]

    # Now make all combinations, replacing N operators by 0
    operator_combinations = itertools.combinations( unroll_operators, comb_scheme )

    rwgt_points = []
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
        full_set = np.full( (len(all_operators), 2), '0', dtype = 'object' )
        full_set[:len(unique_names), :] = op_arr 

        # Fill with those that are turned OFF
        unused_operators = np.array(
                [ (op[0], '0.0') for op in all_operators if op[0] not in unique_names ]
        )
        full_set[len(unique_names):, :] = unused_operators

        # A bit of OCD but let's sort the full matrix by operator name
        full_set = full_set[full_set[:, 0].argsort()]

        # Make sure we do not count twice the same point
        rwgt_points.append( full_set )
       
    return rwgt_points 

def get_rwgt_name( rwgt_point ):

    rwgt_name = "_".join( 
        "{0}{1}".format( opname, opval.replace(".", "p").replace("-","minus") ) for opname, opval in rwgt_point if opval != "0.0"
    )

    if not any( np.array(rwgt_point[:, 1], dtype = float) ):
        return "SM"
    return rwgt_name
