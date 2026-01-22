"""
cmgrdf_datasets
---------------
Utilities to translate dataset YAML + hooks into CMGRDF process definitions.
"""

# CMGRDF libraries
from CMGRDF import MCGroup, MCSample, Process,  Source
from copy import deepcopy
from utils import load_config, get_logger
import sys
from CMGRDF.modifiers import Append
from CMGRDF import AddWeight

logger = get_logger( __name__ )


def get_cmgrdf_processes( datasets_file, hooks_module ):
    """
    Build and return a list of CMGRDF Process objects from dataset metadata.
    """
    logger.info( "Preparing datasets." )

    samples = datasets_file.get( "mcsamples", [] )
    groupings = build_groupings(samples, hooks_module)
    mc_processes = build_processes(groupings)
    return mc_processes

def get_lumi_dict( configs ):
    """ Return the total luminosity for datasets that are used in the analysis """
    lumi_dict = {}
    for campaign, campaign_file in configs["campaigns"].items():
        campaign_meta = load_config( campaign_file ) 
        lumi_dict[ str(campaign_meta["era"]) ] = float( campaign_meta["lumi"] )
    return lumi_dict


# --- Helper functions --------------------
def resolve_hooks(hooks_module, hooks_list):
    """Return a list of hook callables resolved from hooks_module and hooks_list."""
    if not hooks_module or not hooks_list:
        return []
    return getattr(hooks_module, hooks_list)


def build_source(sample_name, file_path):
    """Create a CMGRDF Source for a single file."""
    return Source(name = f"source_{sample_name}", files = [ file_path ], era = None)


def build_mcsample(sample_meta, file_path, hooks_module, rwgt_hooks = []):
    """Create an MCSample for one input file using sample metadata."""
    sample_name = sample_meta.get("name")
    norm = sample_meta.get("xsec")
    genSum = sample_meta.get("genSum")
    hooks_list = sample_meta.get("hooks")

    hooks = resolve_hooks(hooks_module, hooks_list) + rwgt_hooks
    source_obj = build_source(sample_name, file_path)

    return MCSample(
        name = sample_name,
        source = source_obj,
        xsec = norm,
        eras = None,
        hooks = hooks,
        genSumWeightName = genSum
    )

def build_groupings(samples, hooks_module):
    """
    Parse dataset metadata and return a mapping group_name -> list of MCSample objects.
    """

    groupings = {}

    # Always treat `samples` as a list
    if isinstance(samples, dict):
        samples = [samples]

    for sample in samples:
        base_name = sample.get("name")
        sample_files = sample.get("files", [])
        reweights = sample.get("ReweightingWeights", [])

        # If no reweights, process normally
        if not reweights:
            groupings.setdefault(base_name, [])
            for file_path in sample_files:
                mcsample = build_mcsample(
                    sample,
                    file_path,
                    hooks_module
                )
                groupings[base_name].append(mcsample)

        else:
            # Process all reweighted versions without recursion
            for rw in reweights:
                rw_name = f"{base_name}__weight{rw}"
                groupings.setdefault(rw_name, [])

                # Here you can set the reweighting hook if needed

                reweighting_hook = Append( 
                    AddWeight("point", f"LHEReweightingWeight[{rw}]") 
                )

                rwgt_hooks = [ reweighting_hook ]

                for file_path in sample_files:
                    # Construct a minimal "derived sample" without deepcopy
                    derived = dict(sample)
                    derived["name"] = rw_name

                    mcsample = build_mcsample(
                        derived,
                        file_path,
                        hooks_module,
                        rwgt_hooks,
                    )
                    groupings[rw_name].append(mcsample)

    return groupings


def build_processes(groupings):
    """
    Convert groupings to a list of CMGRDF Process objects (one per group).
    """
    processes = []
    color = 1

    for groupname, group_list in groupings.items():
        logger.info( f"Grouping files into  {groupname}" )

        if not group_list:
            logger.warning( f"Group {groupname} has no samples contributing to it!!! Will skip." )
        else:
            process = Process(
                name = groupname,
                samples = MCGroup( groupname, group_list ),
                fillColor = color,
            )
            processes.append(process)

        color += 1
        if color in [10, 18, 19]:  # skip unreadable/white colors
            color += 1

    return processes


