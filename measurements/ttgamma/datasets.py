""" Define the datasets for the ttG analysis """
import plotting.cms_palette as cmscolors

datasets = {
    "mc" : {
        "TTGSM_Prod" :{
            "legend" : "t#bar{t}#gamma (from production)",
            "processes" : [
                {
                    "name" : "TTG_fromProduction",
                    "files" : "das:/TTGJets_Dilepton_TuneCP5_13TeV-amcatnloFXFX-madspin-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v2/NANOAODSIM",
                    "xsec" : 0.428,
                    "hooks" : "from_prod",
                }
            ]
        },
        "TTGSM_Decay" :{
            # "ReweightPoints" : [ 128 ], # Give a non empty list to enable reweighting to a specific point
            "processes" : [
                {
                    "name" : "TTG_fromDecay",
                    "files" : "das:/TTGamma_Dilept_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
                    "xsec" : 2.22037,
                    "hooks" : "from_decay",
                },
            ]
        },
        "TTGEFT" : {
            "ReweightMap" : "workdirs/combination_20Jan_2026/ttgamma/reweight_mapping.json",
            # "ReweightPoints" : [ 128 ], # Give a non empty list to enable reweighting to a specific point
            "processes" : [
                {
                    "name" : "TTGEFT_fromProd",
                    "files" : "eos:/eos/cms/store/group/phys_top/cvicovil/top-comb/combination_Jan18_2026/NANOGEN/TTG-1Jets-TTto2L2Nu/*.root",
                    "xsec" : 0.428,
                    "hooks" : "from_prod",
                }
            ]
        }
    }
}

