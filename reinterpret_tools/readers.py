"""
readers
-------

Histogram reader utilities: construction and loading of TH1/TH2 readers that
wrap ROOT files and provide a unified API for plotting.

Typical exports:
- build_histogram_readers(datasets_cfg): create reader instances for each
  dataset described in the configuration (used by the replot pipeline).
- load_histograms_for_readers(readers, rfile_path): for a dict of readers,
  load and return the actual ROOT histogram objects (cloned and detached
  from input files).

Readers encapsulate logic for retrieving histograms by name/path, applying
scale factors, and handling missing histograms in a predictable way.
"""

from pathlib import Path
import ROOT

from utils.logger import get_logger
from utils import PlotFileHistogramReader
import utils.auxiliars as aux

logger = get_logger(__name__)


def build_histogram_readers(grouping_cfg):
    """Load grouping definitions and build histogram readers."""
    decorators = aux.load_config(grouping_cfg)["plotting"]["decorators"]

    readers = {}
    for ent in decorators:
        readers[ent["name"]] = PlotFileHistogramReader(
            name=ent["name"],
            label=ent["label"],
            procs=ent["procs"],
            decorations=ent["histo-decorations"],
        )
    return readers


def load_histograms_for_readers(readers, path):
    """Load ROOT histograms."""
    invalid = []
    for name, reader in readers.items():
        reader.load(path)
        if not reader.is_valid():
            invalid.append(name)
    for bad in invalid:
        readers.pop(bad)
    return readers
