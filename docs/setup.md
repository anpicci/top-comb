# Setup TOP EFT Combination

This repository uses several `git submodules` and `Makefiles` to make running combination commands as smooth as possible for newcomers.

To set up the repository, follow these steps:


```bash
git clone https://gitlab.cern.ch/cvicovil/topcomb_analyses.git
make setup
```

When running `make setup`, you will be prompted to choose which set of tools to download.  
This ensures that only the modules required for your specific purpose are fetched. When prompted,
enter a number to select the package you want to download.

The complete list of available submodules can be found in [`.gitmodules`](../.gitmodules).

If you need **all submodules**, you can clone them in one step:

```bash
git clone https://gitlab.cern.ch/cvicovil/topcomb_analyses.git --recursive
```
 
