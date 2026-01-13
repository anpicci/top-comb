"""
Mode builders and registry.

The callable_function is the actual implementation to run for the mode,
and inputs_dict contains keyword arguments that will be passed to it.
"""

import os
import subprocess

def _setup_gen():
    """
    Builder for setting up GEN related aspects 
    """    
    from gen_tools import setup_gen_config
    return setup_gen_config 

def _reinterpret():
    """
    Builder for 'reinterpret' mode.
    """
    from reinterpret_tools import reinterpret
    return reinterpret

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
    "setup": {
        "funcs": [ _setup_gen ],
    },
    "reinterpret": {
        "funcs": [ _reinterpret ],
    },
    "setup_combine": {
        "funcs": [ _setup_combine ],
    },
}