""" Definitions to be used in the TOP-23-002 input """
from CMGRDF import Define
from CMGRDF.collectionUtils import DefineSkimmedCollection, DefineP4
from CMGRDF.plots import Plot
from CMGRDF.flow import Cut

def get_fiducial_partonLevel( args ):
    sequence = [
        Cut( "atleast2genlep", "nFiducialLepton_partonLevel >= 2"),
        Cut( "mll", "(FiducialLepton_partonLevel_p4[0] + FiducialLepton_partonLevel_p4[1]).M() > 30"),
    ]
    return sequence
