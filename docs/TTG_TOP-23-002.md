# Metadata for TOP-23-002
This folder contains information about the TOP-23-002 analysis, and how it is used in the context of the combination.

## Relevant info
 - Contact person: Beatriz Ribeiro Lopes
 - iCMS link: [TOP-23-002](https://cms.cern.ch/iCMS/analysisadmin/cadilines?line=TOP-23-002&tp=an&id=2663&ancode=TOP-23-002)
 - Nominal samples used in the **public** measurement:

| Dataset name | Quick note | Root Request | Das Nano | Gridpack |
| :-------- | :--------: | :-------- | :-------- | :-------- |
| `TTGJets_Dilepton_TuneCP5_13TeV-amcatnloFXFX-madspin-pythia8` | Gamma from production | [McM](https://cms-pdmv-prod.web.cern.ch/mcm/requests?page=0&dataset_name=TTGJets_Dilepton_TuneCP5_13TeV-amcatnloFXFX-madspin-pythia8&member_of_campaign=RunIISummer20UL*wmLHE*)  | [Nano v9](https://cmsweb.cern.ch/das/request?view=list&limit=50&instance=prod%2Fglobal&input=dataset%3D%2F*TTGJets_Dilepton_TuneCP5_13TeV-amcatnloFXFX-madspin-pythia8*%2F*20UL*v9*%2FNANOAODSIM) |  `/cvmfs/cms.cern.ch/phys_generator/gridpacks/UL/13TeV/el9_amd64_gcc11/madgraph/V5_2.9.18/TTGJets_NLO_FXFX/TTGJets_Dilepton_NLO_FXFX_slc7_amd64_gcc10_CMSSW_12_4_8_tarball.tar.xz`  
| `TTGamma_Dilept_TuneCP5_13TeV-madgraph-pythia8` | Gamma from decay | [McM](https://cms-pdmv-prod.web.cern.ch/mcm/requests?page=0&dataset_name=TTGamma_Dilept_TuneCP5_13TeV-madgraph*&member_of_campaign=RunIISummer20UL*wmLHE*)  | [Nano v9](https://cmsweb.cern.ch/das/request?view=list&limit=50&instance=prod%2Fglobal&input=dataset%3D%2F*TTGamma_Dilept_TuneCP5_13TeV-madgraph-pythia8*%2F*20UL*v9*%2FNANOAODSIM) | `/cvmfs/cms.cern.ch/phys_generator/gridpacks/UL/13TeV/madgraph/V5_2.6.5/TTGamma_Dilept/ttGamma_Dilept_5f_ckm_LO_1line_slc7_amd64_gcc700_CMSSW_10_6_19_tarball.tar.xz`  
 
## Overlap removal
Since the signal in this analysis is modeled with two different samples, there is the need of treating the overlap between the two. 

> Photons at the detector-level are matched to their generator-level counterparts, and the requirements are then applied to the generator level photon. From the tt dilepton sample, remove all events containing a photon that fulfils the signal photon definition. From the ttGamma sample, remove all events with no photons fulfilling the signal photon definition.


