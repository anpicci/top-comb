""" Definitions to be used in the TOP-23-002 input """
import ROOT as r 
from CMGRDF import Define
from CMGRDF.collectionUtils import DefineSkimmedCollection, DefineP4
from CMGRDF.plots import Plot
from CMGRDF.flow import Cut

plots = [
    Plot( 
        "genphoton_categories", 
        "genphoton_category", 
        (32, 0, 32), 
        xTitle = "Generator level photon categories (parton level)", legend = "TR", unit = "", 
        xBinLabels = ["00000","00001","00010","00011","00100","00101","00110","00111","01000","01001","01010","01011","01100","01101","01110","01111","10000","10001","10010","10011","10100","10101","10110","10111","11000","11001","11010","11011","11100","11101","11110","11111"], 
        do_superwide = True, 
        verticalLabels = True, 
        lines = [
            {"x1": 2, "y1": 1, "x2": 2, "y2": 220000, "coords": "bin", "color": r.kBlack, "style": 1, "width": 2},
            {"x1": 8, "y1": 1, "x2": 8, "y2": 220000, "coords": "bin", "color": r.kBlack, "style": 1, "width": 2},
            {"x1": 9, "y1": 1, "x2": 9, "y2": 220000, "coords": "bin", "color": r.kBlack, "style": 1, "width": 2},
            {"x1": 17, "y1": 1, "x2": 17, "y2": 220000, "coords": "bin", "color": r.kBlack, "style": 1, "width": 2},
        ],
        spams =  [
            #{ "text" : r"0#gamma", "x0" : 0.17, "y0" : 0.79, "x1" : 0.19, "y1" : 0.81, "textsize" : 35 },
            { "text" : r"1#gamma (decay)", "x0" : 0.19, "y0" : 0.65, "x1" : 0.21, "y1" : 0.67, "textsize" : 35 },
            { "text" : r"1#gamma (ISR)", "x0" : 0.40, "y0" : 0.55, "x1" : 0.41, "y1" : 0.57, "textsize" : 35 },
            { "text" : r"1#gamma (offshell)", "x0" : 0.60, "y0" : 0.55, "x1" : 0.61, "y1" : 0.57, "textsize" : 35 },
        ],
        fixYaxismin = 1.,
        fixYaxis = 1e8
    ),
    #Plot( "leading_genphoton_pt", f"FiducialPhoton_partonLevel_pt[0]", (10, 20, 140), xTitle = r"Generator level #it{p}_{T} (#gamma)", legend = "TR", unit = "GeV" ),
    #Plot( "deltaR_pho_closestTop", f"deltaR_pho_closestTop", (14, 0, 5), xTitle = r"Generator level #Delta R (#gamma, closest top)", legend = "TR", unit = "" ),
]
