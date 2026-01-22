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
        "gen_weight", 
        "genWeight", 
        (1, 0.5, 1.5), 
        xTitle = "Nominal generator weight", 
        yTitle = "Events",
        logy = True,
        fixYaxismin = 1.,
    )
]
