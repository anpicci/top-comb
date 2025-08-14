""" Definitions to be used in the TOP-23-002 input """
from CMGRDF import Define
from CMGRDF.collectionUtils import DefineSkimmedCollection
from CMGRDF.plots import Plot

evaluate_function = lambda func, *args : f"{func}({','.join(*args)})"

sequence = [
    # Basic fiducial lepton definition 
    Define(
        "is_fiducial_lepton", 
        evaluate_function(
            "isFiducialLepton",    
            [
                "GenDressedLepton_pt", 
            ]
        ),
        eras = [] 
    ),
    DefineSkimmedCollection(
        "FiducialLepton",
        "GenDressedLepton",
        mask="is_fiducial_lepton",
        members = ( 
            'pt',  
            'eta', 
            'phi', 
            'pdgId'
        ),
        optMembers=[]
    ),

]


plots = [

    Plot(
        "genlep1_pt",
        f"FiducialLepton_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "#it{p}_{T} (lep1) (GeV)",
        legend = "TR",
    )

]
