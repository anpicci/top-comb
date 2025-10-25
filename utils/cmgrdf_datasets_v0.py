"""
Functions to fetch datasets from the information available in the yml files
"""
import os
from copy import deepcopy
import ROOT
import glob
import sys

# CMGRDF libraries
from CMGRDF import MCSample, DataSample, Data, Process, AddWeight, Source
from CMGRDF.modifiers import Append
import importlib

import utils.auxiliars as aux
# Create the logger instance
from utils.logger import get_logger
logger = get_logger( __name__ )

def get_cmgrdf_processes( meta, operators, algorithm ):
    """
    This function is used to read a list of input metadata that contains information
    """

    # First get the reweighting points
    samples = meta['samples'] 
    algos = algorithm.split("-")

    # This is the list of processes that will be included in the histograms
    mc_processes = []

    # Now consider the processes (lines in the histogram)
    all_rwgt_points = [] 
    for algo in algos:
        all_rwgt_points.extend( aux.get_rwgt_points(algo, operators) )
    sm = deepcopy( all_rwgt_points[-1] )
    sm[:, 1] = "0.0"
    all_rwgt_points.append( sm )

    for sample_metadata in samples:
       
        sample_name = sample_metadata['name']
        sample_type = sample_metadata['type']
        sample_files = sample_metadata['files']
        if type(sample_files) == str:
            sample_files = glob.glob( sample_files )

        sample_xsec  = sample_metadata["xsec"]
        sample_hook_module = importlib.import_module( sample_metadata["hookfile"] )
        custom_hooks = []
        for custom_hook in sample_metadata["hooks"]:
            custom_hooks.extend( getattr(sample_hook_module, custom_hook) )

        logger.info( f"Preparing process {sample_name}" )
        source_obj = Source( name = f"source_{sample_name}", files = sample_files, era = "all" )

        if sample_type == "EFT":
            # Now for each combination of operators, create a MCProcess
            for irwgt, rwgt_point in enumerate( all_rwgt_points ):
        
                procname = sample_name + f"_{irwgt}_" + aux.get_rwgt_name( rwgt_point ) 
                logger.debug( f"   - Including reweighting weight: {procname} ( index = {irwgt} )" )
                
                mcsample = MCSample(
                    name = sample_name,
                    source = source_obj,
                    xsec = sample_xsec,
                    eras = None,
                    hooks = [ 
                        Append( AddWeight("point", f"LHEReweightingWeight[{irwgt}]") ) 
                    ] + custom_hooks,
                    genSumWeightName = f"genEventSumw"# * LHEReweightingSumw[{len(all_rwgt_points)}]", # Renorm to SM, which is the last index
                )
                
                proc = Process(
                    name = procname,
                    samples = [ mcsample ], 
                    fillColor = 0,
                    LineColor = irwgt,
                    lineStyle = 1,
                    signal = True
                )
        
                mc_processes.append( proc )
        else:
                mcsample = MCSample(
                    name = sample_name,
                    source = source_obj,
                    xsec = sample_xsec,
                    eras = None,
                    hooks = custom_hooks,
                    genSumWeightName = "genEventSumw", # this has to be changed to the SM
                )
                
                proc = Process(
                    name = sample_name,
                    samples = [ mcsample ], 
                    fillColor = 0,
                    LineColor = 1,
                    lineStyle = 9,
                    signal = True
                )

                mc_processes.append( proc )

    return mc_processes 

