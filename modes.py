"""
Mode builders and registry.

Each builder is a callable that returns a function accepting an environment dict.
"""

import os
import subprocess

def _setup_gen():
    """Builder for setting up GEN related aspects."""
    from gen_tools import setup_gen_config
    return setup_gen_config

def _submit_gen():
    """Builder for setting up GEN related aspects."""
    from gen_tools import submit_gen
    return submit_gen

def _reinterpret():
    """Builder for 'reinterpret' mode."""
    from reinterpret_tools import reinterpret
    return reinterpret

def _setup_combine():
    """Builder for installing combine. Executes a script inside `combine_tools`."""
    def run_combine_install(environment):
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

        cmd = " ".join(options)
        subprocess.check_call(
            cmd,
            shell=True,
            cwd=os.getcwd(),
        )
    
    return run_combine_install

MODE_REGISTRY = {
    # Each entry provides:
    #  - "funcs": list of builders that return a function accepting environment
    "setup": {
        "funcs": [_setup_gen],
    },
    "submit": {
        "funcs": [_submit_gen],
    },
    "reinterpret": {
        "funcs": [_reinterpret],
    },
    "setup_combine": {
        "funcs": [_setup_combine],
    },
}