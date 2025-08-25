# A set of functions that are useful
import yaml
import itertools
import numpy as np
from copy import deepcopy

# Create the logger instance
from utils.logger import get_logger
logger = get_logger( __name__ )


def load_config( config_path ) -> dict:
    """ Loads a configuration file written in yml format """
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def get_rwgt_points(algo, all_operators):
    """ Function to get reweighting points """
    logger.info( f"Making groups of {algo}" )

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
        (op[0], opbound) for op in all_operators  for opbound in op[1:] 
    ]

    # Now make all combinations, replacing N operators by 0
    operator_combinations = itertools.combinations( unroll_operators, r_pars[ algo ] )

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
        "{0}{1}".format( opname, opval.replace(".", "p").replace("-","minus") ) for opname, opval in rwgt_point
    )

    if not any( np.array(rwgt_point[:, 1], dtype = float) ):
        return "SM"
    return rwgt_name
