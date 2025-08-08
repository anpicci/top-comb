**Note**: click [here](https://gitlab.cern.ch/cvicovil/top-comb/-/blob/master/README.md) to return to the main README.
# Analysis Logistics

This document summarizes the inputs required for the combination process.

## TOPCOMB Analysis

The inputs for the combination are maintained in a separate repository: [topcomb_analyses](https://gitlab.cern.ch/cvicovil/topcomb_analyses).  
This repository serves as the bookkeeping hub for all aspects related to the analyses included in the combination.

## Adding a New Analysis
The `topcomb_analyses` repository is designed to store all relevant details for a given analysis in a single configuration file, written in `yml` format.  
This avoids scattering the information in different parts.

A typical `yml` configuration file looks like this:

```yaml
analysis_name:
    XXX

samples:
    # Relevant information for the modeling aspects

operators:
  - [operator_name, reference_point, minBound, maxBound]
  - ... # other operators
```

An example of how one full `yaml` file looks like can be found in the [TTG configuration file](https://gitlab.cern.ch/cvicovil/topcomb_analyses/-/blob/master/configs/TTG_TOP-23-002.yml?ref_type=heads).

**TODO**: provide a script to generate skeletons for `yaml` files, to make it easier for people that want to contribute.

Note that:
 - The `samples` part is mostly relevant for analysis that do not look into EFTs directly, and are reinterpreted in terms of generated NanoGEN MC samples that include the EFT effects. 
 - The `operators` side is generally interesting, as there we decide which couplings get constrained by which analysis. 

## Generating the Analysis Folder

Once the `yaml` file is properly configured, you can automatically generate the analysis folder containing all the necessary files for the combination.  

Run the following command:

```bash
python3 topcomb_analysis/setup_analysis.py --config topcomb_analysis/configs/MY_ANALYSIS.yaml
```

Here, `MY_ANALYSIS.yaml` refers to the configuration file described in the previous section.

