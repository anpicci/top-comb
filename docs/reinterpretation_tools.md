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

### Analyzing NanoGEN Events

The analysis of NanoGEN events is handled using the `cmgrdf-prototype` submodule.  
The main idea is to:

- Use `cmgrdf-prototype` to produce histograms and cards that include both the SM and EFT points.  
- Validate these histograms by comparing them with the samples used in the corresponding differential measurements.

---

#### Step 1: Configure the Analysis

To implement a new analysis, start by setting up the `analysis` tag in the input `yaml` configuration file.  
You can follow the example provided in the [`TTG_TOP-23-002.yml`](https://gitlab.cern.ch/cvicovil/top-comb/-/blob/master/configs/TTG_TOP-23-002.yml?ref_type=heads) file.

A typical configuration looks like this:

```yaml
analysis:
  samples:
    PROC_A:
      path: # Directory where NanoGEN events are stored
      files: # Subfolder(s) in path containing the events. Regex can be used to match multiple paths.
      xsec: # Cross section used to normalize the shapes
    PROC_B:
      path: # Directory where NanoGEN events are stored
      files: # Subfolder(s) in path containing the events. Regex can be used to match multiple paths.
      xsec: # Cross section used to normalize the shapes
  plugins: [
    # C++ plugins that define fiducial selections or other analysis functions
  ]
  definitions: # Sequence of steps to reproduce fiducial selections
  plots: # List of observables and histograms to be produced
  outpath: # Directory where output histograms and plots will be stored
```

Where:
- **Processes (`PROC_A`, `PROC_B`, ...)**  
  Define the processes to include in the analysis.  
  For example, you may want to compare the SM point of `ttGamma` where the photon originates either from the production or from the decay.  
  All `files` listed under a process are combined and normalized using the same cross section.  

  *Note*: This interface is still evolving, and some caveats may arise when performing more detailed validations.
- **Plugins**  
  The `plugins` section specifies C++ functions that reproduce fiducial selections or provide additional functionality (e.g., defining observables or new RDataFrame columns).  

  - Typically, plugins for a given analysis are stored in the `plugins` directory.  
  - It is also recommended to leverage existing configurations provided in `cmgrdf-prototype/src`.
- **Definitions**  
  The `definitions` section describes the sequence of analysis steps.  
  It is essentially Python code that builds a list of variable and collection definitions, making use of functions defined in the C++ plugins.

- **Plots**  
  The `plots` section specifies which observables and histograms should be produced as output.

- **Outpath**  
  The `outpath` field sets the directory where the resulting histograms and plots will be saved.


