"""
loaders
-------

Small utilities to import Python modules by path and to ensure external
dependencies (e.g. the CMGRDF submodule) are present and up-to-date.

This module typically exposes:
- load_module_from_path(name, path): import a module given a filesystem path
  (used for per-analysis `plots` and `hooks` modules).
- update_cmgrdf_submodule(): update/initialise the vendor CMGRDF submodule so
  compiled components and headers are available.

Functions intentionally keep behavior minimal and raise informative exceptions
when expected files or directories are missing.
"""

import subprocess
import importlib.util

from utils.logger import get_logger

logger = get_logger(__name__)


def update_cmgrdf_submodule():
    """git submodule update."""
    try:
        subprocess.run(
            ["git", "submodule", "update", "--init", "cmgrdf-prototype"],
            check=True
        )
        logger.info("Successfully updated cmgrdf submodule.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error updating cmgrdf: {e}")


def load_module_from_path(name, path):
    """Load module from filesystem path."""
    print( path )
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
