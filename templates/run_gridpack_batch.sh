#!/bin/bash

# Template script for batch submission of gridpacks
BASE=`pwd`

tar -xvf cards.tgz

# Download genproductions
git clone https://gitlab.cern.ch/cms-gen/genproductions_scripts.git -b master 

# Basic setup
cd genproductions_scripts/bin/MadGraph5_aMCatNLO
cp -r $BASE/__CARDSDIR__ . 


# Run generation
./gridpack_generation.sh __PROCNAME__ __CARDSDIR__

# Now prepare the output path
OUTPATH=__OUTPATH__/top-comb/__PROCNAME__/gridpack
mkdir -p $OUTPATH 

mv __PROCNAME__*tar.xz $OUTPATH
mv __PROCNAME__*log $OUTPATH

date=$(date '+%Y-%m-%d %H:%M:%S')

echo $date > $OUTPATH/VERSION
