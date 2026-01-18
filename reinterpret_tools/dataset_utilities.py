"""
cmgrdf_datasets
---------------
Utilities to read datasets and return CMGRDF process objects.
"""
import glob
import subprocess
from typing import Dict, List, Optional, Any

from CMGRDF import (
    Data,
    MCGroup, 
    MCSample, 
    Process,  
    Source,
    DataSample,
    Append,
    AddWeight
)
from utils.auxiliars import load_config
from utils.logger import get_logger

logger = get_logger(__name__)


def read_datasets(era: str, datasets_module: Any, hooks_module: Any) -> List[Process]:
    """
    Build and return a list of CMGRDF Process objects from dataset metadata.
    
    Args:
        era: Data-taking era identifier
        datasets_module: Module containing dataset definitions
        hooks_module: Module containing hook functions
        
    Returns:
        List of MC Process objects
    """
    logger.info("Preparing datasets.")
    all_datasets = getattr(datasets_module, "datasets", {})

    mc_datasets = get_mc_datasets(era, all_datasets["mc"], hooks_module)

    processes = build_processes(
        all_datasets, 
        {**mc_datasets}
    )

    return processes

# --- Helper functions --------------------
def _fetch_from_das(dataset_pattern: str) -> List[str]:
    """
    Fetch file list from DAS for a given dataset pattern.
    
    Args:
        dataset_pattern: DAS dataset name pattern
        
    Returns:
        List of file paths with redirector prefix
    """
    result = subprocess.run(
        ["dasgoclient", "-query", f"file dataset={dataset_pattern}"],
        capture_output=True,
        text=True,
        check=True
    )
    
    files = result.stdout.strip().split("\n")
    # Filter out empty strings and add redirector prefix
    redirector = "root://cms-xrd-global.cern.ch/"
    return [redirector + f for f in files if f]

    
def _fetch_from_eos(dataset_pattern: str) -> List[str]:
    """
    Fetch file list from EOS for a given dataset pattern.
    
    Args:
        dataset_pattern: EOS directory path pattern
        
    Returns:
        List of ROOT file paths
    """
    return glob.glob(dataset_pattern)

    
def resolve_hooks(hooks_module: Optional[Any], hooks_list: Optional[List[str]]) -> Optional[List]:
    """
    Return a list of hook callables resolved from hooks_module and hooks_list.
    
    Args:
        hooks_module: Module containing hook functions
        hooks_list: List of hook names to resolve
        
    Returns:
        List of hook callables or None
    """
    if not hooks_module or not hooks_list:
        return None
    return getattr(hooks_module, hooks_list, None)


def _create_source(era: str, sample_name: str, files: List[str]) -> Dict[str, Source]:
    """
    Create a Source object dictionary for a sample.
    
    Args:
        era: Data-taking era
        sample_name: Name of the sample
        files: List of file paths
        
    Returns:
        Dictionary mapping era to Source object
    """
    return {
        era: Source(
            name=f"source_{sample_name}", 
            files=files, 
            era=era
        )
    }


def _resolve_files(files: str) -> List[str]:
    """
    Resolve file paths based on prefix (das:/ or eos:/).
    
    Args:
        files: File path string with prefix
        
    Returns:
        List of resolved file paths
    """
    if isinstance(files, str):
        if files.startswith("das:/"):
            return _fetch_from_das(files[4:])
        elif files.startswith("eos:/"):
            return _fetch_from_eos(files[4:])
    return []

def get_mclist(dataset: Dict[str, Any], hooks_module, era, reweighting_hooks = [], genSum = "genEventSumw") -> List[MCSample]:
    """
    Create a list of MCSample objects for a dataset without reweighting.
    """
    mclist = []
    processes = dataset.get("processes", [])
    logger.debug(f" - Processes: {', '.join(proc.get('name') for proc in processes)}.")
    for proc in processes:

        sample_files = _resolve_files(proc.get("files"))
        sample_name = proc.get("name")
        norm = proc.get("xsec")
        hooks = resolve_hooks(hooks_module, proc.get("hooks"))
        source_obj = _create_source(era, sample_name, sample_files)

        mcsample = MCSample(
            name=sample_name,
            source=source_obj,
            xsec=norm,
            eras=[ era ],
            hooks = hooks+ reweighting_hooks,
            genSumWeightName=genSum,
        )

        mclist.append(mcsample)

    return mclist



def get_mc_datasets(era: str, mc_datasets: Dict[str, Any], hooks_module: Any) -> Dict[str, List]:
    """
    Process and return MC datasets grouped by name.
    
    Args:
        era: Data-taking era
        mc_datasets: Dictionary of MC dataset configurations
        hooks_module: Module containing hook functions
        
    Returns:
        Dictionary mapping dataset names to lists of MCSample objects
    """
    groups = {}

    for dataset_name, dataset in mc_datasets.items():
        reweights = dataset.get("ReweightPoints", [])

        if len(reweights) == 0:
            logger.info(f"Grouping {dataset_name}.")
            groups.setdefault(dataset_name, [])
            groups[dataset_name] = get_mclist( dataset, hooks_module, era )
        else:            
            # Process all reweighted versions without recursion
            for rw in reweights:
                rw_name = f"{dataset_name}__weight{rw}"
                logger.info(f"Grouping {rw_name}.")
                groups.setdefault(rw_name, [])

                # Here you can set the reweighting hook if needed

                reweighting_hook = Append( 
                    AddWeight("point", f"LHEReweightingWeight[{rw}]") 
                )

                rwgt_hooks = [ reweighting_hook ]
                groups[rw_name] = get_mclist( 
                    dataset, 
                    hooks_module, 
                    era, 
                    reweighting_hooks = rwgt_hooks,
                    genSum = f"genEventSumw*LHEReweightingSumw[{rw}]"
                )

    return groups


def build_processes(samples, groupings: Dict[str, List]) -> List[Process]:
    """
    Convert groupings to a list of CMGRDF Process objects (one per group).
    
    Args:
        groupings: Dictionary mapping group names to lists of samples
        
    Returns:
        List of Process objects
    """
    processes = []

    for groupname, group_list in groupings.items():
        logger.info(f"Grouping files into {groupname}")

        if not group_list:
            logger.warning(f"Group {groupname} has no samples contributing to it! Will skip.")
            continue

        sample_meta = samples["mc"].get(groupname.split("__weight")[0])
        process = Process(
            name=groupname,
            samples=MCGroup(groupname, group_list),
            fillColor = sample_meta.get("histo-decorations").get("SetFillColor")
        )
            
        processes.append(process)
        
    return processes


