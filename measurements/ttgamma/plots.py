""" Plots to be used in the TOP-23-002 input """
from CMGRDF.plots import Plot
plots = [
    Plot( 
        "tot_weight", 
        "1", 
        (1, 0.5, 1.5), 
        xTitle = "Number of events", 
        yTitle = "Events / bin",
        fixYaxismin = 1.,
    ),
    Plot( 
        "pho1pt", 
        "FiducialPhoton_particleLevel_p4[0].Pt()", 
        [20,35,50,70,130,1000], 
        xTitle = "p_{T}(#gamma_{1}) [GeV]", 
        yTitle = "Events / bin",
        fixYaxismin = 1.,
    ),
    Plot( 
        "LHERwgt0", 
        "LHEReweightingWeight[0]", 
        (10, 0.5, 1.5), 
        xTitle = "Reweigting weight [0]", 
        yTitle = "Events",
        logy = True,
        fixYaxismin = 1.,
    ),
    Plot( 
        "LHERwgt128", 
        "LHEReweightingWeight[128]", 
        (10, 0.5, 1.5), 
        xTitle = "Reweigting weight [128]", 
        yTitle = "Events",
        logy = True,
        fixYaxismin = 1.,
    )
]
