"""
Functions to fetch datasets from the information available in the yml files
"""
import os
import ROOT

# CMGRDF libraries
from CMGRDF import MCSample, DataSample, Data, Process, AddWeight
from CMGRDF.modifiers import Append

import utils.auxiliars as aux
# Create the logger instance
from utils.logger import get_logger
logger = get_logger( __name__ )

def get_cmgrdf_processes( meta ):
    """
    This function is used to read a list of input metadata that contains information
    """

    # First get the reweighting points
    files = meta['analysis']['samples'] 
    operators = meta['operators']['scans']
    algorithm = meta['operators']['algo']
    algos = algorithm.split("-")


    # This is the list of processes that will be included in the histograms
    mc_processes = []

    # Now consider the processes (lines in the histogram)
    all_rwgt_points = [] 
    for algo in algos:
        all_rwgt_points.extend( aux.get_rwgt_points(algo, operators) )

    for sample_name, sample_metadata in files.items():

        # Now for each combination of operators, create a MCProcess
        for irwgt, rwgt_point in enumerate( all_rwgt_points ):
    
            procname = aux.get_rwgt_name( rwgt_point ) 
        
            files = sample_metadata["files"]
            norm  = sample_metadata["xsec"]
            mcpath = sample_metadata["path"]
        
            logger.info( f"Preparing process {sample_name}" )

            # First load all the files that make up this sample
            sourcepath = f"{mcpath}/{files}"
            logger.info( f"Including MC sample: xsec = {norm}, fileIn = {sourcepath})" )
            logger.info( f"Including reweighting weight: {procname} ( index = {irwgt} )" )
            
            mcsample = MCSample(
                name = sample_name,
                source = sourcepath,
                xsec = norm,
                eras = [ "all" ],
                hooks = [ 
                    Append( AddWeight("point", f"LHEReweightingWeight[{irwgt}]") ) 
                ],
                genSumWeightName = "genEventSumw * LHEReweightingSumw[ 0 ]", # this has to be changed to the SM
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
        
    
    return mc_processes 

