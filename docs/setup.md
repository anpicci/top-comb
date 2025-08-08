**Note**: click [here](https://gitlab.cern.ch/cvicovil/top-comb/-/blob/master/README.md) to return to the main README.

# Setup TOP EFT Combination

This repository uses several `git submodules` and `Makefiles` to make running combination commands as smooth as possible for newcomers.

To set up the repository, follow these steps:

1. Clone everything
  ```bash
  git clone https://gitlab.cern.ch/cvicovil/topcomb_analyses.git
  make setup
  ```
  
  When running `make setup`, you will be prompted to choose which set of tools to download.  This ensures that only the modules required for your specific purpose are fetched. When prompted, enter a number to select the package you want to download.
  
  The complete list of available submodules can be found in [`.gitmodules`](../.gitmodules). If you need **all submodules**, you can clone them in one step:
  
  ```bash
  git clone https://gitlab.cern.ch/cvicovil/topcomb_analyses.git --recursive
  ```
2. Source the main environment

This is needed everytime you want to work with the tools used in the combination. To do this, just run:

```bash
source setenv.sh
```

This will essentially load different environment variables that are used in the combination scripts.

 
