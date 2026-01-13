"""
cmgrdf_datasets
---------------
Utilities to read datasets and return CMGRDF process objects.
"""
from CMGRDF import MCGroup, MCSample, Process,  Source
from utils import load_config, get_logger
import glob
import sys
from CMGRDF.modifiers import Append
from CMGRDF import AddWeight
import subprocess

logger = get_logger( __name__ )


def read_datasets( datasets_module, hooks_module ):
    """
    Build and return a list of CMGRDF Process objects from dataset metadata.
    """
    logger.info( "Preparing datasets." )

    groupings = build_groupings(datasets_module, hooks_module)
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
def _fetch_from_das( 
        dataset_pattern: str  
    ):
   
    files = subprocess.run(
        [
            "dasgoclient",
            "-query",
            f"file dataset={dataset_pattern}"
        ],
        capture_output = True,
    )
    file_list = files.stdout.decode("utf-8").strip().split("\n")

    # Now for each file we have to add the redirector prefix
    redirector = "root://cms-xrd-global.cern.ch/"
    file_list = [ redirector + f for f in file_list ][:10]  # avoid empty string case
    return file_list
    
def _fetch_from_eos(
        dataset_pattern: str
    ):
    files = glob.glob( dataset_pattern )
    return files[:10]
    
def resolve_hooks(hooks_module, hooks_list):
    """Return a list of hook callables resolved from hooks_module and hooks_list."""
    if not hooks_module or not hooks_list:
        return []
    return getattr(hooks_module, hooks_list)

def build_mcsample(sample_meta, files, hooks_module, genSum = "genEventSumw", rwgt_hooks = []):
    """Create an MCSample for one input file using sample metadata."""
    sample_name = sample_meta.get("name")
    norm = sample_meta.get("xsec")
    hooks_list = sample_meta.get("hooks")

    hooks = resolve_hooks(hooks_module, hooks_list) + rwgt_hooks
    source_obj = Source(
        name = f"source_{sample_name}", 
        files = files, 
        era = None
    )

    return MCSample(
        name = sample_name,
        source = source_obj,
        xsec = norm,
        eras = None,
        hooks = hooks,
        genSumWeightName = genSum
    )

def build_groupings(datasets_module, hooks_module):
    """
    Parse dataset metadata and return a mapping group_name -> list of MCSample objects.
    """

    groupings = {}

    datasets = getattr(datasets_module, "datasets", {})


    for dataset in datasets:
        dataset_name = dataset.get("name")
        sample_files = dataset.get("files", [])
        if isinstance(sample_files, str) and sample_files.startswith("das:/"):
            sample_files = _fetch_from_das( sample_files[4:] )
        elif isinstance(sample_files, str) and sample_files.startswith("eos:/"):
            sample_files = _fetch_from_eos( sample_files[4:] ) 

        reweights = dataset.get("ReweightingWeights", [])

        # If no reweights, process normally
        if not reweights:
            groupings.setdefault(dataset_name, [])
            
            mcsample = build_mcsample(
                dataset,
                sample_files,
                hooks_module
            )
            groupings[ dataset_name ].append(
                mcsample
            )

            print(f"Added dataset {dataset_name} with {len(sample_files)} files.")

        else:
            # Process all reweighted versions without recursion
            for rw in reweights:
                rw_name = f"{dataset_name}__weight{rw}"
                groupings.setdefault(rw_name, [])

                # Here you can set the reweighting hook if needed

                reweighting_hook = Append( 
                    AddWeight("point", f"LHEReweightingWeight[{rw}]") 
                )
                genSum = f"genEventSumw*LHEReweightingSumw[{rw}]"

                rwgt_hooks = [ reweighting_hook ]

                # Construct a minimal "derived sample" without deepcopy
                derived = dict(dataset)
                derived["name"] = rw_name

                mcsample = build_mcsample(
                    derived,
                    sample_files,
                    hooks_module,
                    genSum,
                    rwgt_hooks,
                )
                groupings[rw_name].append(
                    mcsample
                )

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


