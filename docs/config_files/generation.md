# Generation config — how to write generation.yml

This document explains the structure and semantics of the generation YAML used by the generation-related modes (setup_gen, run_gridpack, run_nanogen). For a concrete example refer to [configs/ttgamma/generation.yml](../../configs/ttgamma/generation.yml).

Example snippet (conceptual):
```yaml
samples:
  - name: MYPROC
    load_extramodels: mymodel.tar.gz
    model: mymodel
    process:
      - 'define p = g u c d s u~ c~ d~ s~ b b~'
      - 'generate p p > t t~ a'
    template_run_card:
      name: templates/run_card.dat
    template_customizecards:
      name: templates/customizecards.dat
      extraopts:
        - "set run_card nevents 100000"
    fragment:
      name: templates/pythia_fragment.dat
      process_parameters:
        - "'TimeShower:mMaxGamma = 4.0'"
```

* **name**: identifier for the sample. 
* **load_extramodels**: to access models that are not installed by default in Madgraph. The list of available models in genproductions can be found [here](https://cms-project-generators.web.cern.ch/cms-project-generators/).
* **model**: name of the model to be imported in the madgraph `process` card.
* **process**: MadGraph commands that define and generate the process. 
* **template_\* cards**: additional cards to be used by MadGraph. The logic is implemented in a templated fashion, so we only have to worry about specific process configurations, while keeping all the basic skeletons to configure madgraph frozen for the user.
  * `run_card`: controls basic running configurations. Parameters in the `run_card` used during gridpack generation can be modified by using the customization card.
  * `customizecards`: additional per-process configurations. They enter the generation as MadGraph commands (e.g. `set run_card ptj XX`) would set the parameter `ptj` to a value of XX, changing it from the default value that one can find in the `template_run_card`.
  * `restrict_card`: additional restrictions to be applied to the madgraph model. 
* **fragment**: Path to a parton-shower / fragment template. The templates can be modified with additional parameters using the `process_parameters` block.
