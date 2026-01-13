import os
import re
import subprocess
import ROOT
import argparse
import time

# Create the logger instance
from logger import get_logger
logger = get_logger( __name__ )

cwd = os.getcwd()

def add_parsing_options():
    """ This is a custom parser that allows for passing options to the code """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--inpath', 
        dest = "inpath", 
        default = ".", 
        help = "Path with batch outputs."
    )
    parser.add_argument(
        '--nevents', 
        dest = "nevents_per_file", 
        default = 5000000, 
        type = int,
        help = "Path with batch outputs."
    )
    parser.add_argument(
        '--submit', 
        dest = "submit", 
        action = 'store_true',
        help = "Actually submit jobs to condor (only used with --use-condor). Without this flag, only creates wrappers and submit files."
    )
    parser.add_argument(
        '--ncores', 
        dest = "ncores", 
        default = 1,
        type = int,
        help = "Number of cores to run with (only for local execution)."
    )
    parser.add_argument(
        '--dry-run', 
        dest = "dry_run", 
        action = 'store_true',
        help = "Print actions without executing them."
    )
    return parser.parse_args()

def get_events_in_file(filename, treename="Events"):
    """Return number of entries in the given ROOT file for the specified tree."""
    try:
        f = ROOT.TFile.Open(filename)
        if not f or f.IsZombie():
            logger.warning(f"could not open {filename}")
            return 0
        tree = f.Get(treename)
        if not tree:
            logger.warning( f"{filename} has no tree named {treename}" )
            return 0
        entries = tree.GetEntries()
        f.Close()
        return entries
    except Exception as e:
        logger.error(f"Reading {filename}: {e}")
        return 0

def log_chunk_events(outfolder, files, treename="Events", dry_run=False):
    """Write a log file with per-file and total event counts before moving files."""
    if not dry_run:
        os.makedirs(outfolder, exist_ok=True)
    log_path = os.path.join(outfolder, "log.txt")
    total_events = 0
    lines = []

    # Files can be either a list of paths or list of tuples (path, batch_num)
    for item in files:
        f = item[0] if isinstance(item, tuple) else item
        nevents = get_events_in_file(f, treename)
        lines.append(f"{f}: {nevents} events")
        total_events += nevents

    lines.append(f"total: {total_events} events")

    if dry_run:
        logger.info(f"[DRY RUN] Would write log to {log_path}:")
        for line in lines:
            logger.info(f"  {line}")
    else:
        with open(log_path, "w") as logfile:
            logfile.write("\n".join(lines) + "\n")
        logger.info(f"Wrote log to {log_path}")

def move_files_to_chunk(outfolder, input_files, dry_run=False):
    """Move input files into a dedicated chunk folder, renaming from GEN.root to GEN_batchNUMBER.root."""
    logger.debug(f"Moving {len(input_files)} files -> {outfolder}")
    if not dry_run:
        os.makedirs(outfolder, exist_ok=True)
    else:
        logger.info(f"[DRY RUN] Would create directory: {outfolder}")
    
    for item in input_files:
        # Handle both (filepath, batch_num) tuples and plain filepaths
        if isinstance(item, tuple):
            file, batch_num = item
            dest_name = f"GEN_batch{batch_num}.root"
            dest_path = os.path.join(outfolder, dest_name)
            if dry_run:
                logger.info(f"[DRY RUN] Would execute: mv {file} {dest_path}")
            else:
                logger.warning(f"  - Moving {file} -> {dest_path}")
                subprocess.run(["mv", file, dest_path], check=True)
        else:
            file = item
            dest_path = os.path.join(outfolder, os.path.basename(file))
            if dry_run:
                logger.info(f"[DRY RUN] Would execute: mv {file} {dest_path}")
            else:
                logger.warning(f"  - Moving {file}")
                subprocess.run(["mv", file, outfolder], check=True)

def group_files(inpath, target_events, treename="Events", dry_run=False):
    """Group ROOT files into new chunk folders, without touching existing ones."""
    os.chdir(inpath)
    
    # Find all batchNUMBER directories
    batch_dirs = [d for d in os.listdir(".") if os.path.isdir(d) and re.match(r"batch\d+", d)]
    
    if not batch_dirs:
        logger.warning( f"There are no batch directories for merging in {inpath}. Skipping" )
        return None
    
    # Sort batch directories by batch number
    batch_dirs.sort(key=lambda x: int(re.findall(r"\d+", x)[0]))
    
    # Collect files with their batch numbers
    files = []
    for batch_dir in batch_dirs:
        gen_file = os.path.join(batch_dir, "GEN.root")
        if os.path.exists(gen_file):
            batch_num = re.findall(r"\d+", batch_dir)[0]
            files.append((gen_file, batch_num))
        else:
            logger.warning(f"No GEN.root found in {batch_dir}")
    
    if not files:
        logger.warning( f"There are no GEN.root files for merging in {inpath}. Skipping" )
        return None

    logger.info(f"Found {len(files)} files")

    current_group = []
    current_events = 0
    output_index = 0

    if not dry_run:
        os.makedirs("problematic_files", exist_ok=True)
    else:
        logger.info("[DRY RUN] Would create directory: problematic_files")
    
    output_prefix = os.getcwd().split("/")[-1]

    # Find the next free chunk index
    while os.path.exists(f"{output_prefix}_{output_index}_chunks"):
        logger.info(f"Skipping existing chunk folder {output_prefix}_{output_index}_chunks")
        output_index += 1

    for f, batch_num in files:
        logger.info( f"Reading file: {f} ({batch_num})" )
        nevents = get_events_in_file(f, treename)
        if nevents == 0:
            if dry_run:
                logger.info(f"[DRY RUN] Would execute: mv {f} problematic_files/")
            else:
                subprocess.run(["mv", f, "problematic_files/"], check=True)
            continue

        if current_events + nevents > target_events and current_group:
            output_name = f"{output_prefix}_{output_index}.root"
            outfolder = output_name.replace(".root", "_chunks")

            # Only create if it doesn't exist
            if not os.path.exists(outfolder):
                log_chunk_events(outfolder, current_group, treename, dry_run=dry_run)

                move_files_to_chunk(outfolder, current_group, dry_run=dry_run)
            else:
                logger.info(f"Skipping {outfolder} (already exists)")

            output_index += 1
            current_group = []
            current_events = 0

            # Move past any existing chunk folders
            while os.path.exists(f"{output_prefix}_{output_index}_chunks"):
                logger.info(f"Skipping existing chunk folder {output_prefix}_{output_index}_chunks")
                output_index += 1

        current_group.append((f, batch_num))
        current_events += nevents

    # Handle last group
    if current_group:
        output_name = f"{output_prefix}_{output_index}.root"
        outfolder = output_name.replace(".root", "_chunks")

        if not os.path.exists(outfolder):
            log_chunk_events(outfolder, current_group, treename, dry_run=dry_run)
            move_files_to_chunk(outfolder, current_group, dry_run=dry_run)
        else:
            logger.info(f"Skipping {outfolder} (already exists)")


def create_condor_wrapper(temp_dir):
    """Create a wrapper script for condor to execute merge jobs."""
    wrapper_path = os.path.join(temp_dir, "condor_merge_wrapper.sh")
    with open(wrapper_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# HTCondor wrapper for merging ROOT files\n\n")
        f.write("CHUNK_FOLDER=$1\n")
        f.write("OUTPUT_NAME=$2\n")
        f.write("WORKDIR=$3\n\n")
        f.write("cd $WORKDIR/$CHUNK_FOLDER\n\n")
        f.write("FILES=(*.root)\n")
        f.write('if [ ${#FILES[@]} -eq 0 ]; then\n')
        f.write('    echo "No ROOT files to merge"\n')
        f.write('    exit 1\n')
        f.write('fi\n\n')
        f.write("HADDNANO=/cvmfs/cms.cern.ch/el9_amd64_gcc12/cms/cmssw/CMSSW_14_0_6/bin/el9_amd64_gcc12/haddnano.py\n\n")
        f.write('if [ -f "../$OUTPUT_NAME" ]; then\n')
        f.write('    echo "Output file $OUTPUT_NAME already exists. Skipping."\n')
        f.write('    exit 0\n')
        f.write('fi\n\n')
        f.write('echo "Merging ${FILES[@]} into $OUTPUT_NAME"\n')
        f.write('$HADDNANO $OUTPUT_NAME "${FILES[@]}"\n')
        f.write('mv $OUTPUT_NAME ..\n')
        f.write('echo "Merge complete"\n')
    
    os.chmod(wrapper_path, 0o755)
    logger.info(f"Created condor wrapper script: {wrapper_path}")
    return wrapper_path


def create_condor_submit_file(inpath, chunk_folders, temp_dir):
    """Create HTCondor submit file for merge jobs."""
    submit_file = os.path.join(temp_dir, "merge_jobs.sub")
    wrapper_script = os.path.join(temp_dir, "condor_merge_wrapper.sh")
    
    with open(submit_file, "w") as f:
        f.write("# HTCondor submit file for merging ROOT files\n")
        f.write("universe = vanilla\n")
        f.write(f"executable = {wrapper_script}\n")
        f.write("should_transfer_files = NO\n")
        f.write("+JobFlavour = \"workday\"\n\n")
        
        for folder in chunk_folders:
            output_name = folder.replace("_chunks", ".root")
            log_dir = os.path.join(temp_dir, "condor_logs")
            os.makedirs(log_dir, exist_ok=True)
            
            f.write(f"arguments = {folder} {output_name} {inpath}\n")
            f.write(f"output = {log_dir}/{folder}.out\n")
            f.write(f"error = {log_dir}/{folder}.err\n")
            f.write(f"log = {log_dir}/{folder}.log\n")
            f.write("queue\n\n")
    
    logger.info(f"Created condor submit file: {submit_file}")
    return submit_file

def merge_all_chunks_condor(inpath, submit=False):
    """Submit merge jobs to HTCondor."""
    os.chdir(cwd)
    chunk_folders = [d for d in os.listdir( inpath ) if d.endswith("_chunks")]
    
    if not chunk_folders:
        logger.warning("No chunk folders found to merge")
        return
    
    logger.info(f"Found {len(chunk_folders)} chunk folders to merge")
    
    # Extract sample name from inpath
    sample_name = inpath.split("/")[-1] 
    
    # Create temporary directory for condor files
    temp_dir = os.path.join("merge_temp", sample_name)
    os.makedirs(temp_dir, exist_ok=True)
    logger.info(f"Created temporary directory for condor files: {temp_dir}")
    
    # Create wrapper script and submit file
    create_condor_wrapper(temp_dir)
    submit_file = create_condor_submit_file(inpath, chunk_folders, temp_dir)
    
    if not submit:
        logger.info("Dry run mode: wrapper and submit files created but jobs NOT submitted")
        logger.info(f"To submit jobs, run: condor_submit {submit_file}")
        logger.info(f"Or re-run with --submit flag")
        return
    
    # Submit to condor
    logger.info(f"Submitting {len(chunk_folders)} jobs to HTCondor...")
    result = subprocess.run(["condor_submit", submit_file], capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info("Jobs submitted successfully!")
        logger.info(result.stdout)
    else:
        logger.error(f"Failed to submit jobs: {result.stderr}")
        return
    
    logger.info("Monitor jobs with: condor_q")
    logger.info(f"Check logs in: {os.path.join(temp_dir, 'condor_logs')}")


if __name__ == "__main__":
    opts = add_parsing_options()
    inpath = opts.inpath
    target_events = opts.nevents_per_file
    ncores = opts.ncores
    submit = opts.submit
    dry_run = opts.dry_run

    if dry_run:
        logger.info("=== DRY RUN MODE - No files will be moved ===")

    # Step 1: group files into folders
    group_files(inpath, target_events, dry_run=dry_run)

    # Step 2: merge all chunk folders
    logger.info("Preparing HTCondor merge jobs...")
    merge_all_chunks_condor(inpath, submit=submit)
