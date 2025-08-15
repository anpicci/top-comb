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

    # First, fetch all the nanogen files and prepare the MCSamples
    mc_samples = {}


    for sample_name, sample_metadata in files.items():
        
        files = sample_metadata["files"]
        norm  = sample_metadata["xsec"]
        mcpath = sample_metadata["path"]
        
        logger.info( f"Preparing process {sample_name}" )
        
        samples = []
        for ifile, _file in enumerate( files ):
            fileName = f"{sample_name}_batch{ifile}" 
            sourcepath = f"{mcpath}/{_file}"
            logger.info( f"Including MC sample: {fileName} (xsec : {norm}, fileIn = {sourcepath})" )
        
            sample = MCSample(
                name = fileName,
                source = sourcepath,
                xsec = norm,
                eras = [ "all" ],
                genSumWeightName = "genEventSumw",
                signal = False 
            )
        
            samples.append( sample )

        mc_samples[ sample_name ] = samples
        

    for algo in algos:
        rwgt_points = aux.get_rwgt_points(algo, operators)

        # Now for each combination of operators, create a MCProcess
        for irwgt, rwgt_point in enumerate( rwgt_points ):

            procname = aux.get_rwgt_name( rwgt_point ) 
            proc = Process(
                name = procname,
                samples = samples,
                fillColor = 0,
                LineColor = irwgt,
                lineStyle = 1,
                hooks = [ 
                    Append( AddWeight("point", f"LHEReweightingWeight[{irwgt}]") ) 
                ]
            )

            mc_processes.append( proc )
        
    
    return mc_processes 

