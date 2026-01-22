# Generation instructions

This document explains how to use the generation-related modes of the top-comb driver: `submit`, which is used to submit MC generation jobs to HTCondor.

## Prerequisites
- Define the generation aspects for your analysis. Instructions on how to setup the `generation.yml` files can be found in this [document](docs/config_files/generation.md)
- tmg-mc-validation for `nanogen` submission if required by your setup.

## Commands / Examples

Create gridpacks (uses prepared configs under the workdir):
```bash
python3 top-comb.py --tag $NAME submit -w gridpack -m $MEASUREMENT [--submit]
```

Run NanoGEN generation:
```bash
python3 top-comb.py --tag $NAME submit -w nanogen -m $MEASUREMENT [--submit] [--j $NJOBS] [-n $NEVENTS_PER_JOB]
```

This will lunch everything into HTCondor and save the outputs in a predefined folder where all combination results are stored. See [docs/environment.md](../docs/environment.md)
