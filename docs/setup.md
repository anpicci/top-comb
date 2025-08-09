**Note**: click [here](https://gitlab.cern.ch/cvicovil/top-comb/-/blob/master/README.md) to return to the main README.

# Setup TOP EFT Combination

This repository uses several `git submodules` and `Makefiles` to make running combination commands as smooth as possible for newcomers. **Once cloned**, and each time wants to run **anything** (either gridpack creation, generating events, or running the combination), one needs to setup the environment by doing:

```bash
source setenv.sh
```

**Important**: the default path where outputs from batch jobs (such as generation of events) is fixed to `/eos/cms/store/group/phys_top/cvicovil/`, so if you plan to generate events, change this path in the `setenv.sh` script in the main repository. 

As for how to set up the repository, follow **one of these options**:

## Clone everything at once
The complete list of available submodules can be found in [`.gitmodules`](../.gitmodules). If you need **all submodules**, you can clone them in one step:

```bash
git clone https://gitlab.cern.ch/cvicovil/topcomb_analyses.git --recursive
```

## Clone everything and install specific packages

This is normally only needed if for whichever reason one does not need to install `topcomb_analyses` (e.g. for just generating events or producing differential level studies). Normally, it is best to install everything (since the whole project is anyway not heavy). 

```bash
git clone https://gitlab.cern.ch/cvicovil/topcomb_analyses.git
make setup
```

When running `make setup`, you will be prompted to choose which set of tools to download.  This ensures that only the modules required for your specific purpose are fetched. When prompted, enter a number to select the package you want to download. 
