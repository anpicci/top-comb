#!/bin/bash

# Template script for batch submission of gridpacks

# Unpack genproductions utilities
tar -xvf genproductions.tar.xz
cd MadGraph5_aMCatNLO
./gridpack_generation.sh __PROCNAME__ __CARDSDIR__

# Now prepare the output path
OUTPATH=__OUTPATH__/top-comb/__PROCNAME__/gridpack
mkdir -p $OUTPATH 

mv __PROCNAME__*tar.xz $OUTPATH
