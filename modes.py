"""
Mode builders and registry.

Each builder (e.g. _setup_gen) is a small factory that returns a tuple:
    (callable_function, inputs_dict)

The callable_function is the actual implementation to run for the mode,
and inputs_dict contains keyword arguments that will be passed to it.
"""

import os
import subprocess

def _setup_gen( environment ):
    """
    Builder for setting up GEN related aspects 
    """    
    from gen_tools import setup_gen_config
    return setup_gen_config, {
        "analysis_name" : environment.get("analysis_name"),
        "analysis_meta" : environment.get("main_config"),
        "workdir" : environment.get("workdir"),
        "outpath" : environment.get("outpath"),
        "tmgtools_path" : environment.get("tmgtools"),
        "genprod_repo" : environment.get("genproductions_repo"),
        "genprod_image" : environment.get("genproductions_image"),
        "genprod_branch" : environment.get("genproductions_branch"),
    }

def _gridpack( environment ):
    """
    Builder for gridpack mode 
    """
    from gen_tools import run_gridpack
    return run_gridpack, {
        "workdir": environment.get("workdir"),
        "process": environment.get("process"),
        "submit" : environment.get("submit")
    }

def _nanogen( environment ):
    """
    Builder for run_nanogen mode.
    """
    from gen_tools import run_nanogen
    return run_nanogen, {
        "workdir": environment.get("workdir"),
        "tmgtools_path" : environment.get("tmgtools"),
        "campaign" : environment.get("tmgtools_campaign"),
        "submit" : environment.get("submit"),
        "process": environment.get("process")
    }

def _reinterpret( environment ):
    """
    Builder for 'reinterpret' mode.
    """
    from reinterpret_tools import reinterpret
    return reinterpret, {
        "just_replot": environment.get("just_replot"),
        "outpath" : environment.get("outpath"),
        "workdir" : environment.get("workdir"),
        "ncores" : environment.get("ncores"),
        "debug" : environment.get("debug"),
        "doUnc" : environment.get("doUnc")
    }

def _setup_combine( environment ):
    """
    Builder for installing combine. Just executes a script inside `combine_tools`. 
    """
    script = f"{environment.get('mainpath')}/combine_tools/install_combine.sh"
    options = [
            # Singularity mounting points
            "singularity run",
            "-B /afs -B /eos -B /cvmfs -B /etc/grid-security -B /etc/pki/ca-trust",
            "--home $PWD:$PWD",

            # Script
            f"{environment.get('combine_image')} {script}",

            # Arguments
            "-p", environment.get('mainpath'),
            "-a", environment.get('combine_scram'),
            "-r", environment.get('combine_cmsrel'),
            "-b", environment.get('combine_comb_branch'),
            "-c", environment.get('combine_ch_branch'),
    ]

    cmd = " ".join( options )
    def run( cmd ):
        subprocess.check_call( 
            cmd,
            shell = True, 
            cwd = os.getcwd(), 
        )
        
    return run, { "cmd": cmd }
 
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
    "setup_combine": {
        "funcs": [ _setup_combine ],
        "per-analysis": False,
    },
}