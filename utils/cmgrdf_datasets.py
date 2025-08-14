"""
Functions to fetch datasets
"""

"""
Datasets (based on WZ analysis)
--------------------------------------------------------------
This code builds a series of functions that are useful to read input
ROOT files for both Data and MC. 

The code can be easily debugged by just doing:
python3 datasets.py

from within the folder in which it is contained (and of course, one
needs to load the CMGRDF environment beforehand.)


The order in which you should be reading this code is:

  1. L236 (or approx, might change if we write and don't update this line :D ) 
  2. function `get_cmgrdf_processes`
  3. Continue following that thread until the code finishes doing stuff.
"""

import os
import ROOT

from CMGRDF import MCSample, DataSample, Data, Process

def color_msg(msg, color = "none", indentlevel=0):
    """ Prints a message with ANSI coding so it can be printout with colors """
    codes = {
        "none" : "0m",
        "green" : "1;32m",
        "red" : "1;31m",
        "blue" : "1;34m",
        "yellow" : "1;33m"
    }

    if indentlevel == 0: indentSymbol=">> "
    if indentlevel == 1: indentSymbol="+ "
    if indentlevel >= 2: indentSymbol="* "

    indent = indentlevel*" " + indentSymbol
    print("\033[%s%s%s \033[0m"%(codes[color], indent, msg))
    return


def get_cmgrdf_processes( files ):
    """
    `get_cmgrdf_process`: this function is used to:
        - Read a list of input metadata that contains information
          about the samples.
        - Create CMGRDF MCSample objects and processes for MC samples.
    """
    
    mc_processes = []
    
    for sample_name, sample_metadata in files.items():
        
        files = sample_metadata["files"]
        norm  = sample_metadata["xsec"]
        mcpath = sample_metadata["path"]
        
        color_msg( f"Preparing process {sample_name}", color = "green", indentlevel = 0)
        
        samples = []
        for ifile, _file in enumerate( files ):
            
            fileName = f"{sample_name}_batch{ifile}" 
            sourcepath = f"{mcpath}/{_file}"
            color_msg( f"Including MC sample: {fileName} (xsec : {norm}, fileIn = {sourcepath})", color = "none", indentlevel = 1)
        
            sample = MCSample(
                name = fileName,
                source = sourcepath,
                xsec = norm,
                eras = [ "all" ],
                genSumWeightName = "genEventSumw",
                signal = False 
            )
        
            samples.append( sample )
        
        proc = Process(
            name = sample_name,
            samples = samples,
            fillColor = 0,
            LineColor = 1,
            lineStyle = 1
        )
        
        mc_processes.append( proc )
        
    
    return mc_processes 

