# Amazing chatgpt script to check inconsistencies in reweighting cards...
import sys, os, re
import itertools
import argparse

from settings import TopCombSettings
settings = TopCombSettings().model_dump()

sys.path.append( settings.get("topcomb_mainpath", ".") )

# Create the logger instance
from utils import get_logger
logger = get_logger( __name__ )

def parse_blocks(lines):
    blocks = []
    current = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("launch --rwgt_name="):
            if current:
                blocks.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks

def extract_couplings(blocks):
    """Extract all couplings names present in any block."""
    couplings = set()
    for block in blocks:
        for line in block[1:]:
            if line.startswith("set "):
                parts = line.split()
                if len(parts) >= 2:
                    couplings.add(parts[1])
    return sorted(couplings)

def normalize_block(block):
    """Return a normalized string representation of a block for comparison."""
    launch = block[0]
    sets = sorted(block[1:])  # order of 'set' lines shouldn't matter
    return launch + "\n" + "\n".join(sets)


def check_duplicates(blocks):
    seen = {}
    duplicates = []
    for i, block in enumerate(blocks):
        norm = normalize_block(block)
        if norm in seen:
            duplicates.append((seen[norm], i))
        else:
            seen[norm] = i

    if not duplicates:
        logger.info("No duplicate reweighting blocks found!")
    else:
        logger.error("Duplicate blocks detected:")
        for first, second in duplicates:
            logger.warning(f"  Block {second+1} is a duplicate of block {first+1}")
            logger.warning(f"  -- Block {first+1}:")
            logger.debug( blocks[first] )
            logger.warning(f"  -- Block {second+1}:")
            logger.debug( blocks[second] )

def check_double_modifications(blocks):
    problems = []
    for i, block in enumerate(blocks):
        seen_couplings = {}
        for line in block[1:]:
            if line.startswith("set "):
                parts = line.split()
                if len(parts) >= 2:
                    coupling = parts[1]
                    if coupling in seen_couplings:
                        problems.append((i, coupling))
                    else:
                        seen_couplings[coupling] = True

    if not problems:
        logger.info("No duplicate modification of the same coulping in the same block found!")
    else:
        logger.error("Multiple modifications detected:")
        for block_idx, coupling in problems:
            logger.warning(f"  Coupling '{coupling}' modified more than once in block {block_idx+1}")

def check_sm(blocks):
    """Check that there is at least one block where all couplings are set to 0 (SM) """
    for i, block in enumerate(blocks):
        all_zero = True
        for line in block[1:]:
            if line.startswith("set "):
                parts = line.split()
                if len(parts) >= 3:
                    value = parts[2]
                    try:
                        if float(value) != 0.0:
                            all_zero = False
                            break
                    except ValueError:
                        all_zero = False
                        break

    if all_zero:
        logger.info("At least one block implements the SM prediction.")
    else:
        logger.error("There is no SM point in this reweighting card!!!!.")

def get_nonzero_couplings(block, with_values=False):
    """Return list of couplings with non-zero values in a block.
       If with_values=True, return dict {coupling: float(value)}."""
    nonzeros = {} if with_values else []
    for line in block[1:]:
        if line.startswith("set "):
            parts = line.split()
            if len(parts) >= 3:
                name, value = parts[1], parts[2]
                try:
                    val = float(value)
                    if val != 0.0:
                        if with_values:
                            nonzeros[name] = val
                        else:
                            nonzeros.append(name)
                except ValueError:
                    pass
    return nonzeros


def check_all_couplings_nonzero(blocks, couplings):
    """Check that every coupling has been set to a non-zero value at least once."""
    covered = set()
    for block in blocks:
        nonzeros = get_nonzero_couplings(block)
        if len(nonzeros) == 1:  # only consider blocks with a single variation
            covered.update(nonzeros)
    missing = set(couplings) - covered
    if not missing:
        logger.info("All couplings have been set to non-zero at least once!")
    else:
        logger.error("The following couplings were never set to non-zero:")
        for c in sorted(missing):
            logger.warning(f"  {c}")

def check_all_pairs_nonzero(blocks, couplings):
    """Check that every pair of couplings has appeared non-zero together at least once."""
    required_pairs = set(itertools.combinations(couplings, 2))
    seen_pairs = set()
    for block in blocks:
        nonzeros = get_nonzero_couplings(block)
        for pair in itertools.combinations(sorted(nonzeros), 2):
            seen_pairs.add(pair)
    missing = required_pairs - seen_pairs

    if not missing:
        logger.info("All pairs of couplings have been set to non-zero together at least once!")
    else:
        logger.error("The following coupling pairs never appear non-zero together:")
        for c1, c2 in sorted(missing):
            logger.warning(f"  {c1}, {c2}")

def check_consistent_variations(blocks, couplings):
    """Check that for each coupling, the positive and negative variations are consistent across all blocks."""
    inconsistencies = []
    values_by_coupling = {c: {"pos": set(), "neg": set()} for c in couplings}

    for block in blocks:
        vals = get_nonzero_couplings(block, with_values=True)
        for c, v in vals.items():
            if v > 0:
                values_by_coupling[c]["pos"].add(v)
            elif v < 0:
                values_by_coupling[c]["neg"].add(v)

    for c, sides in values_by_coupling.items():
        if len(sides["pos"]) > 1:
            inconsistencies.append((c, "positive", sorted(sides["pos"])))
        if len(sides["neg"]) > 1:
            inconsistencies.append((c, "negative", sorted(sides["neg"])))


    if not inconsistencies:
        logger.info("All couplings have consistent positive and negative variations across blocks.")
    else:
        logger.error("❌ Inconsistent variations detected:")
        for c, side, vals in inconsistencies:
            logger.warning(f"  Coupling '{c}' has inconsistent {side} variations: {vals}")



def add_parsing_options():
    """ This is a custom parser that allows for passing options to the code """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--card', 
        dest = "card", 
        help = "Card to be checked"
    )
    return parser.parse_args()


if __name__ == "__main__":
    opts = add_parsing_options()
    logger.info( f"Checking reweightin card {opts.card}" )

    with open( opts.card, "r" ) as incard: 
        lines = incard.readlines()
    blocks = parse_blocks(lines)

    # Get coupling names
    couplings = extract_couplings(blocks)

    # Check for duplicates
    check_duplicates( blocks )

    # Check for double modifications
    check_double_modifications( blocks )

    # Check that the SM is there
    check_sm( blocks )

    # Check all couplings have been modified at least once
    check_all_couplings_nonzero(blocks, couplings)

    # Check all combinations of two couplings have been covered
    check_all_pairs_nonzero(blocks, couplings)

    # Check that all couplings are modified consistently
    check_consistent_variations(blocks, couplings)
