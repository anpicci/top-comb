""" Define the datasets for the ttG analysis """
import plotting.cms_palette as cmscolors

datasets = {
    "mc" : {
        "TTG_fromDecay" :{
            "ReweightPoints" : [],
            "legend" : "t#bar{t}#gamma (from decay)",
            "histo-decorations" : {
                "SetFillColor" : cmscolors.orange,
            },
            "processes" : [
                {
                    "name" : "TTG_fromDecay",
                    "files" : "das:/TTGamma_Dilept_TuneCP5_13TeV-madgraph-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
                    "xsec" : 2.22037,
                    "hooks" : "from_decay",
                }
            ]
        },
        "TTG_fromProduction" : {
            "ReweightPoints" : [],
            "legend" : "t#bar{t}#gamma (from prod)",
            "histo-decorations" : {
                "SetFillColor" : cmscolors.light_blue,
            },
            "processes" : [
                {
                    "name" : "TTG_fromProduction",
                    "files" : "das:/TTGJets_Dilepton_TuneCP5_13TeV-amcatnloFXFX-madspin-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v2/NANOAODSIM",
                    "xsec" : 0.428,
                    "hooks" : "from_prod",
                }
            ]
        },
        "TTGEFT_fromDecay" : {
            "ReweightPoints" : [128],
            "legend" : "t#bar{t}#gamma (from decay)",
            "histo-decorations" : {
                "SetFillColor" : cmscolors.dark_orange,
            },
            "processes" : [
                {
                    "name" : "TTGEFT_fromDecay",
                    "files" : "eos:/eos/cms/store/group/phys_top/cvicovil/top-comb/ttgamma/TTto2L2NuGamma/GEN/*.root",
                    "xsec" : 2.22037,
                    "hooks" : "from_decay",
                }
            ]
        },
        "TTGEFT_fromProd" : {
            "ReweightPoints" : [128],
            "legend" : "t#bar{t}#gamma (from production)",
            "histo-decorations" : {
                "SetFillColor" : cmscolors.blue,
            },
            "processes" : [
                {
                    "name" : "TTGEFT_fromProd",
                    "files" : "eos:/eos/cms/store/group/phys_top/cvicovil/top-comb/ttgamma/TTG-1Jets-TTto2L2Nu/GEN/*.root",
                    "xsec" : 0.428,
                    "hooks" : "from_prod",
                }
            ]
        }
    }
}

