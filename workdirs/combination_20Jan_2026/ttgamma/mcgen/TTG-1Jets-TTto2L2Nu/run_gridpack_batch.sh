#!/bin/bash

# Template script for batch submission of gridpacks
BASE=`pwd`

tar -xvf cards.tgz

# Download genproductions
git clone https://gitlab.cern.ch/cvicovil/genproductions_scripts.git -b topcomb_eft_mg265 

# Basic setup
cd genproductions_scripts/bin/MadGraph5_aMCatNLO
cp -r $BASE/mgcards . 

# Run generation
singularity run  -B /afs -B $BASE -B /eos -B /cvmfs -B /etc/grid-security -B /etc/pki/ca-trust --home $PWD:$PWD /cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el7:x86_64 $(echo $(pwd)/gridpack_generation.sh TTG-1Jets-TTto2L2Nu mgcards)
mv *tar.xz $BASE/gridpack.tar.xz
date=$(date '+%Y-%m-%d %H:%M:%S')
echo "The gridpack has been generated $date using https://gitlab.cern.ch/cvicovil/genproductions_scripts.git/topcomb_eft_mg265" > $BASE/VERSION
