""" Define the datasets for the ttG analysis """

datasets = [
    {
        "name" : "TTG_fromDecay",
        "files" : "das:/TTGamma_Dilept_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
        "xsec" : 2.22037,
        "hooks" : "from_decay",
        "genSum" : "genEventSumw"
    },
    {
        "name" : "TTG_fromProduction",
        "files" : "das:/TTGJets_Dilepton_TuneCP5_13TeV-amcatnloFXFX-madspin-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v2/NANOAODSIM",
        "xsec" : 0.428,
        "hooks" : "from_prod",
        "genSum" : "genEventSumw"
    },
    {
        "name" : "TTG_EFT_fromDecay",
        "files" : "eos:/eos/cms/store/group/phys_top/cvicovil/top-comb/ttgamma/TTto2L2NuGamma/GEN/*.root",
        "xsec" : 2.22037,
        "hooks" : "from_decay",
        "genSum" : "genEventSumw",
        "ReweightingWeights" : [128]
    },
    {
        "name" : "TTG_EFT_fromProd",
        "files" : "eos:/eos/cms/store/group/phys_top/cvicovil/top-comb/ttgamma/TTG-1Jets-TTto2L2Nu/GEN/*.root",
        "xsec" : 0.428,
        "hooks" : "from_prod",
        "genSum" : "genEventSumw",
        "ReweightingWeights" : [128]
    }
]

