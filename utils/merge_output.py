import os
import re
import subprocess
import ROOT
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse

# Create the logger instance
from utils import get_logger
logger = get_logger( __name__ )


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
        default = 1000000, 
        type = int,
        help = "Path with batch outputs."
    )
    parser.add_argument(
        '--ncores', 
        dest = "ncores", 
        default = 1,
        type = int,
        help = "Number of cores to run with."
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

def log_chunk_events(outfolder, files, treename="Events"):
    """Write a log file with per-file and total event counts before moving files."""
    os.makedirs(outfolder, exist_ok=True)
    log_path = os.path.join(outfolder, "log.txt")
    total_events = 0
    lines = []

    for f in files:
        nevents = get_events_in_file(f, treename)
        lines.append(f"{f}: {nevents} events")
        total_events += nevents

    lines.append(f"total: {total_events} events")

    with open(log_path, "w") as logfile:
        logfile.write("\n".join(lines) + "\n")

    logger.info(f"Wrote log to {log_path}")

def move_files_to_chunk(outfolder, input_files):
    """Move input files into a dedicated chunk folder."""
    logger.debug(f"Moving {len(input_files)} files -> {outfolder}")
    os.makedirs(outfolder, exist_ok=True)
    for file in input_files:
        logger.warning(f"  - Moving {file}")
        subprocess.run(["mv", file, outfolder], check=True)

def merge_chunk_folder(outfolder, output_name):
    """Run haddnano to merge files in outfolder into output_name."""
    cwd = os.getcwd()
    os.chdir(outfolder)

    files = [f for f in os.listdir(".") if f.endswith(".root")]
    if not files:
        logger.warning(f"No ROOT files to merge in {outfolder}")
        os.chdir(cwd)
        return None

    cmd = (
        "/cvmfs/cms.cern.ch/el9_amd64_gcc12/cms/cmssw/CMSSW_14_0_6/bin/"
        "el9_amd64_gcc12/haddnano.py"
    )
    logger.warning(f"Running {cmd} {output_name} {' '.join(files)}")
    subprocess.run([cmd, output_name] + files, check=True)
    subprocess.run(["mv", output_name, ".."], check=True)

    os.chdir(cwd)
    return os.path.join(outfolder, output_name)


def group_files(inpath, target_events, treename="Events"):
    """Group ROOT files into new chunk folders, without touching existing ones."""
    os.chdir(inpath)
    files = [f for f in os.listdir(".") if re.match(r"out.*\.root", f)]
    files.sort(key=lambda x: int(re.findall(r"\d+", x)[0]))

    logger.info(f"Found {len(files)} files")

    current_group = []
    current_events = 0
    output_index = 0

    os.makedirs("problematic_files", exist_ok=True)
    output_prefix = os.getcwd().split("/")[-1]

    # Find the next free chunk index
    while os.path.exists(f"{output_prefix}_{output_index}_chunks"):
        logger.info(f"Skipping existing chunk folder {output_prefix}_{output_index}_chunks")
        output_index += 1

    for f in files:
        nevents = get_events_in_file(f, treename)
        if nevents == 0:
            subprocess.run(["mv", f, "problematic_files/"], check=True)
            continue

        if current_events + nevents > target_events and current_group:
            output_name = f"{output_prefix}_{output_index}.root"
            outfolder = output_name.replace(".root", "_chunks")

            # Only create if it doesn't exist
            if not os.path.exists(outfolder):
                log_chunk_events(outfolder, current_group, treename)

                move_files_to_chunk(outfolder, current_group)
            else:
                logger.info(f"Skipping {outfolder} (already exists)")

            output_index += 1
            current_group = []
            current_events = 0

            # Move past any existing chunk folders
            while os.path.exists(f"{output_prefix}_{output_index}_chunks"):
                logger.info(f"Skipping existing chunk folder {output_prefix}_{output_index}_chunks")
                output_index += 1

        current_group.append(f)
        current_events += nevents

    # Handle last group
    if current_group:
        output_name = f"{output_prefix}_{output_index}.root"
        outfolder = output_name.replace(".root", "_chunks")

        if not os.path.exists(outfolder):
            log_chunk_events(outfolder, current_group, treename)
            move_files_to_chunk(outfolder, current_group)
        else:
            logger.info(f"Skipping {outfolder} (already exists)")


def merge_all_chunks(inpath, max_workers=1):
    """Iterate over all _chunks folders in inpath and merge their files."""
    os.chdir(inpath)
    chunk_folders = [d for d in os.listdir(".") if d.endswith("_chunks")]

    jobs = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for folder in chunk_folders:
            output_name = folder.replace("_chunks", ".root")
            jobs.append(executor.submit(merge_chunk_folder, folder, output_name))

        for future in as_completed(jobs):
            try:
                result = future.result()
                if result:
                    logger.info(f"Created {result}")
            except Exception as e:
                logger.error(f"{e}")


if __name__ == "__main__":
    opts = add_parsing_options()
    inpath = opts.inpath
    target_events = opts.nevents_per_file
    ncores = opts.ncores

    # Step 1: group files into folders
    group_files(inpath, target_events)

    # Step 2: merge all chunk folders (can be run later/independently)
    merge_all_chunks(inpath, max_workers=ncores)

