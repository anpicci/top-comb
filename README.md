# TOP EFT Combination Repository

This repository contains the scripts, tools, and workflows used to perform the combination of several Top EFT analyses. The combination includes both direct searches for new physics (such as TOP-22-006) and indirect constraints obtained from the reinterpretation of unfolded observables in differential measurements.

## Basic setup
This repository uses several submodules. The full list of available submodules can be found in the [`.gitmodules`](../.gitmodules) file.
If you need **all submodules**, you can clone the repository and initialize them in a single step:

```bash
git clone ssh://git@gitlab.cern.ch:7999/cvicovil/top-comb.git --recursive
```

To create a fresh new install, run:

```bash
python3 top-comb.py  --tag $NAME  setup -m $MEASUREMENT
```
This will create a new folder under `workdirs/$NAME` with all the ingredients to run the combination. The list of available measurements can be found in [the main.yml](./main.yml) file inside this repository.

# Repository structure
This repository is used for three different purposes:
* [Generation of custom NanoGEN tier samples](docs/generation.md).
* Reinterpretation of fiducial selections with EFT injection.
* Combination of multiple analysis using `COMBINE`.

A more detailed explanation on the logic behind how the code runs can be found in the [modes](docs/modes.md) instructions. 


## Talks in CMS meetings
- Carlos' talk in the TOP EFT roundtable (13/11/2025):  
  https://indico.cern.ch/event/1601613/#7-top-eft-combination
- Carlos' talk in the TOP EFT meeting (26/07/2025):  
  https://indico.cern.ch/event/1570261/#2-kickoff-discussion-for-top-e
- Sergio's talk in the TOP PAG Workshop in Ghent (29/01/2025):  
  https://indico.cern.ch/event/1473617/timetable/?view=standard#11-towards-a-top-eft-combinati

## Internal meetings
 - [22/01/2026](https://indico.cern.ch/event/1636542/)
   - Update on current status. First EFT combination with the TOP-23-002 measurement.
   - Planification towards the TOP Workshop in Oviedo
 - [9/12/2025](https://indico.cern.ch/event/1619487/)
   - Update on current status. Most of the reinterpretation part already done.