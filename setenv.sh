#!/bin/bash

# CHANGE THIS!
export TOPCOMB_OUTPATH=/eos/cms/store/group/phys_top/cvicovil/


# Other
export TOPCOMB_MAINPATH=`pwd`
export TOPCOMB_INPUTS=`realpath inputs`
export TOPCOMB_GENPRODUCTIONS=`realpath genproductions_scripts`
export TOPCOMB_CMGRDF=`realpath cmgrdf-prototype`


export SINGULARITY_IMAGE_GRIDPACK=/cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el7:x86_64
export GENPRODUCTIONS_GRIDPACK=https://gitlab.cern.ch/cvicovil/genproductions_scripts.git
export BRANCH_GRIDPACK=topcomb_eft_mg265
