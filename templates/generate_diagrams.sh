#!/bin/bash

# Template script for batch submission of gridpacks
BASE=`pwd`

tar -xvf cards.tgz

# Download genproductions
git clone __GENPRODUCTIONS_GRIDPACK__ -b __BRANCH_GRIDPACK__ 

# Basic setup
cd genproductions_scripts/bin/MadGraph5_aMCatNLO
cp -r $BASE/__CARDSDIR__ . 
cp $BASE/index.php . 

# --- Remove the -nojpg option from the process card
sed -i 's|-nojpeg||g' __CARDSDIR__/__PROCNAME___proc_card.dat

# Run generation
singularity run  -B /afs -B $BASE -B /eos -B /cvmfs -B /etc/grid-security -B /etc/pki/ca-trust --home $PWD:$PWD __SINGULARITY_IMAGE__ $(echo $(pwd)/gridpack_generation.sh __PROCNAME__ __CARDSDIR__  diagrams dummy CODEGEN )

# Move to the directory where the diagram .ps files are found
pushd diagrams/__PROCNAME__/__PROCNAME___gridpack/work/__PROCNAME__ 

# First convert each one in pdf
for subprocess in $(ls -d SubProcesses/P*); do

  for psfile in $( ls -d $subprocess/*ps ); do
    ps2pdf $psfile $psfile.pdf
  done
  # Unite the pdfs
  subprocessname=$( echo $subprocess | awk -F '/' '{print $NF}')
  pdfunite $subprocess/*pdf FDs_${subprocessname}.pdf 

done

# Now copy the Feynman Diagrams to the output path 
OUTPATH=__OUTPATH__/__ANALYSIS_NAME__/__PROCNAME__/gridpack/FeynmanDiagrams/
mkdir -p $OUTPATH/ 
mv FD*pdf $OUTPATH/

popd
# Copy the index.php file to the output directory recursively
find __OUTPATH__ -type d -exec cp -n index.php {} \;

date=$(date '+%Y-%m-%d %H:%M:%S')
echo "Feynman diagrams been generated $date using __GENPRODUCTIONS_GRIDPACK__/__BRANCH_GRIDPACK__" > $OUTPATH/VERSION
