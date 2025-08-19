**Note**: click [here](https://gitlab.cern.ch/cvicovil/top-comb/-/blob/master/README.md) to return to the main README.
# Reinterpretation Tools

This section describes the tools available for reinterpreting differential measurements in the context of EFTs.  
Only the technical aspects are covered here, GEN-level validation must be performed by the user.

## Generation of NanoGEN Events

In the `yml` configuration file described in the [Analysis Logistics](docs/analysis_logistics.md) document, you can specify the settings for generating events in [NanoGEN](https://twiki.cern.ch/twiki/bin/viewauth/CMS/NanoGen) format. This configuration can include:

- Instructions for generating a gridpack for a given signal.
- Settings for the parton shower step.

These steps can be combined to model EFT effects as alternative samples. The resulting samples can then be compared with the unfolded results, allowing direct comparisons between the unfolded data and alternative model predictions. 

There are two steps for this:

### Creating a Gridpack
To create a gridpack, run:

```bash
source setenv.sh
make run
```

- You will be presented with a menu of available actions. Select the **`Gridpack`** option to create a gridpack.
- Next, you will be shown a list of available processes for which gridpacks can be generated.  This list is taken from the official sample definitions in `inputs`.
- New gridpacks can be added by modifying (not recommended) an existing analysis, or setting up a new one. In all cases, following the instructions from [Analysis Logistics](docs/analysis_logistics.md) document.
- The command won't submit any job, but rather it will prepare the configuration files to generate a gridpack. In the end you will be prompted you have to run in case you want to run the gridpack in HTCondor. 


### Creating NanoGEN Events

Once the gridpack is created, you can use it to generate events for comparison with unfolded data. To do this, simply run:

```bash
source setenv.sh # If you haven't done this first
make run
```
 
and select the option `Nanogen`. You will then be shown the command required to launch the job.

The generation of `NanoGEN` events is managed through the `tmg-tools` submodule. This tool automates the submission of multiple HTCondor jobs to generate the requested number of events. Its input is a `JSON` configuration file that specifies both the batch submission parameters and the fragment needed for event generation.   If your analysis was created using the `setup_analysis.py` script, the required configuration file is automatically generated at `inputs/MY_ANALYSIS/PROCESS/nanogen_config.json`. By default, jobs are configured to generate **1M events**, split across **1000 jobs**. You can change these settings by editing the `nanogen_config.json` file.

**Note**: The `tmg-tools` package requires a JSON input file to manage submissions (its scope is broader than the top-combination). We adapt to that convention here, but one is free to submit jobs in whichever way you prefer.

**TODO**: one could improve the way the gridpack is parsed in the fragment, instead of fixing it from the beginning.
