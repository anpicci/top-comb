""" Plots to be used in the TOP-23-002 input """
from CMGRDF.plots import Plot
plots = [
    Plot( 
        "pho1pt", 
        "FiducialPhoton_particleLevel_p4[0].Pt()", 
        [20,35,50,70,130,195], 
        xTitle = "p_{T}(#gamma_{1}) [GeV]", 
        yTitle = "Events / bin",
        fixYaxismin = 1.,
    ),
]
