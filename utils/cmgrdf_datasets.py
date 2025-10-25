# CMGRDF libraries
from CMGRDF import MCGroup, MCSample, DataSample, Data, Process, AddWeight, Source
from CMGRDF.modifiers import Append
import importlib

# Create the logger instance
from utils.logger import get_logger
import utils.auxiliars as aux
import utils.cms_pallete as pallete
import sys

logger = get_logger( __name__ )

def get_lumi_dict( configs ):
    """ Return the total luminosity for datasets that are used in the analysis """
    lumi_dict = {}
    for campaign, campaign_file in configs["campaigns"].items():
        campaign_meta = aux.load_config( campaign_file ) 
        lumi_dict[ str(campaign_meta["era"]) ] = float( campaign_meta["lumi"] )
    return lumi_dict


def get_cmgrdf_processes( datasets_file, hooks_module = None ):
    """
    This function is used to read a list of input metadata that contains information
    """
    groupings = {} 

    logger.info( f"Preparing datasets." )
    
    # --- Fill MC samples
    for group_meta in datasets_file["mcsamples"]: 
        group = group_meta["group_name"]
        procs = group_meta["procs"]
        groupings[group] = []
        for sample_meta in procs:
            # Unpack the relevant information
            sample_name = sample_meta["name"]
            files = sample_meta["files"]
            norm  = sample_meta["xsec"]
            genSum  = sample_meta["genSum"]

            # Possibility to add hooks, which are preprocessing modules basically.
            hooks = []
            if sample_meta["hooks"] and hooks_module:
                hooks = getattr(hooks_module, sample_meta["hooks"]) 

            for file in files:
                source_obj = Source( name = f"source_{sample_name}", files = [ file ], era = None)
            
                logger.info( f"Loading sample {sample_name} -- norm: {norm}" )

                # An MCSample per input 
                mcsample = MCSample(
                    name = sample_name,
                    source = source_obj,
                    xsec = norm,
                    eras = None,
                    hooks = hooks,
                    genSumWeightName = genSum 
                )
    
                groupings[group].append( mcsample )

            
    mc = []

    # Now for each group, create a CMGRDF::Process object 
    color = 1
    for groupname, group_list in groupings.items():
        
        logger.info( f"Grouping files into  {groupname}" )
        
        if len(group_list):

            # Add dummy colors since the plan is to plot with an outside script
            process = Process( 
                name = groupname,
                samples = MCGroup( groupname, group_list ),
                fillColor = color,
            )
            mc.append( process )

        else:
            logger.warning( f"Group {groupname} has no samples contributing to it!!! Will skip." )

        color += 1
        if color in [10, 18, 19]: # These are white colors that can't be reaed in a plot
            color += 1
            
    return mc 


