from CMGRDF import Define, Cut

def baseline():
    """ Basic common selection across channels """
    cuts = [ 
        Cut("atleast2genlep","nFiducialLepton_particleLevel >= 2"),
        Cut("atleast2genjet", "nFiducialJet_particleLevel >= 2"),
        Cut("atleast1genbjet", "nFiducialBJet_particleLevel >= 1"),
        Cut("mll",  "(FiducialLepton_particleLevel_p4[0] + FiducialLepton_particleLevel_p4[1]).M() > 30"),
    ]

    return cuts

def nophoton():
    cuts = baseline()
    cuts += [ 
        Cut("nophoton","nFiducialPhoton_particleLevel == 0"),
    ]

    return cuts

def exact1photon():
    cuts = baseline()
    cuts += [ 
        Cut("exact1photon","nFiducialPhoton_particleLevel == 1"),
    ]

    return cuts

def exact2photon():
    cuts = baseline()
    cuts += [ 
        Cut("exact2photon","nFiducialPhoton_particleLevel == 2"),
    ]

    return cuts

def morethan2photon():
    cuts = baseline()
    cuts += [ 
        Cut("morethan2photon","nFiducialPhoton_particleLevel > 2"),
    ]

    return cuts