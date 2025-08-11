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
- New gridpacks can be added by modifying (not recommended) or setting up a new analysis, following the instructions from [Analysis Logistics](docs/analysis_logistics.md) document.

### Creating NanoGEN events
Once the gridpack is created, one can use it to generate events that can be further compared to the unfolded data. To do so, one can simply run:



