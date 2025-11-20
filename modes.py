"""
Mode builders and registry.

Each builder (e.g. _setup_gen) is a small factory that returns a tuple:
    (callable_function, inputs_dict)

The callable_function is the actual implementation to run for the mode,
and inputs_dict contains keyword arguments that will be passed to it.
"""

# === Environment ===
from settings import TopCombSettings
settings = TopCombSettings().model_dump()
import os

def _setup_gen(workdir, args):
    """
    Builder for setting up GEN related aspects 
    """
    from gen_tools import setup_gen_config
    return setup_gen_config, {
        "settings": settings,  # project settings required by the gen tool
        "workdir": os.path.join(workdir, "generation"),  # per-mode workdir
    }

def _gridpack(workdir, args):
    """
    Builder for  
    """
    from gen_tools import run_gridpack
    return run_gridpack, {
        "settings": settings,
        "workdir": os.path.join(workdir, "generation"),
    }

def _nanogen(workdir, args):
    """
    Builder for 'run_nanogen' mode.

    The returned function will perform the lightweight NanoGEN generation
    using prepared gridpacks/samples in the generation workdir.
    """
    from gen_tools import run_nanogen
    return run_nanogen, {
        "settings": settings,
        "workdir": os.path.join(workdir, "generation"),
    }

def _reinterpret(workdir, args):
    """
    Builder for 'reinterpret' mode.

    Reinterpretation runs over the analysis outputs. We pass the parsed
    CLI args as 'opts' so the reinterpret tool can inspect additional
    runtime flags (e.g. --just-replot).
    """
    from reinterpret_tools import reinterpret
    return reinterpret, {
        "workdir": os.path.join(workdir, "analysis"),
        "opts": args,
    }


MODE_REGISTRY = {
    # Each entry provides:
    #  - "funcs": list of builders that return (func, inputs)
    #  - "per-analysis": whether the driver should call the func once per analysis
    "setup": {
        "funcs": [ _setup_gen ],
        "per-analysis": True,
    },
    "run_gridpack": {
        "funcs": [ _gridpack ],
        "per-analysis": True,
    },
    "run_nanogen": {
        "funcs": [ _nanogen ],
        "per-analysis": True,
    },
    "reinterpret": {
        "funcs": [ _reinterpret ],
        "per-analysis": True,
    },
}