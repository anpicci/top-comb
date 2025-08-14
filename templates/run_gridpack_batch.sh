#!/bin/bash

# Template script for batch submission of gridpacks
BASE=`pwd`

tar -xvf cards.tgz

# Download genproductions
git clone __GENPRODUCTIONS_GRIDPACK__ -b __BRANCH_GRIDPACK__ 

# Basic setup
cd genproductions_scripts/bin/MadGraph5_aMCatNLO
cp -r $BASE/__CARDSDIR__ . 

# Run generation
singularity run  -B /afs -B $BASE -B /eos -B /cvmfs -B /etc/grid-security -B /etc/pki/ca-trust --home $PWD:$PWD __SINGULARITY_IMAGE__ $(echo $(pwd)/gridpack_generation.sh __PROCNAME__ __CARDSDIR__)

# Now prepare the output path
OUTPATH=__OUTPATH__/top-comb/__PROCNAME__/gridpack
mkdir -p $OUTPATH 

mv __PROCNAME__*tar.xz $OUTPATH/__PROCNAME__.tar.xz
mv __PROCNAME__*.log $OUTPATH/__PROCNAME__.log

date=$(date '+%Y-%m-%d %H:%M:%S')

echo "The gridpack has been generated $date using __GENPRODUCTIONS_GRIDPACK__/__BRANCH_GRIDPACK__" > $OUTPATH/VERSION
