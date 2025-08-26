# Define hooks for the ttG analysis
from CMGRDF.modifiers import Append
from CMGRDF.flow import Cut
from CMGRDF import Define
from CMGRDF.collectionUtils import DefineSkimmedCollection

evaluate_function = lambda func, args: f"{func}({','.join(args)})"

hooks = [
    Append( 
        Define(
            "is_fiducial_photon_parton_level",
            evaluate_function(
                "isFiducialPhoton_PartonLevel",
                [
                    "GenPart_pdgId",
                    "GenPart_status",
                    "GenPart_pt",
                    "GenPart_eta",
                    "GenPart_phi",
                    "GenPart_genPartIdxMother"
            ],
            ),
        eras=[],
        )
    ),
    Append(
        DefineSkimmedCollection(
            "FiducialPhoton_partonLevel",
            "GenPart",
            mask="is_fiducial_photon_parton_level", # This is defined as a hook
            members=(
                "pt",
                "eta",
                "phi",
                "mass",
                "genPartIdxMother",
                #"iso",
                "pdgId",
                "status",
                "statusFlags"
            ),
            optMembers=[],
        ),
    ),
    Append( 
        Define(
            "genphoton_category",
            evaluate_function(
                "get_genphoton_category",
                [
                    "GenPart_pdgId",
                    "GenPart_genPartIdxMother",
                    "FiducialPhoton_partonLevel_pdgId",
                    "FiducialPhoton_partonLevel_statusFlags",
                    "FiducialPhoton_partonLevel_genPartIdxMother"
            ],
            ),
        eras=[],
        )
    ),    
    Append( Cut( "fromProduction", "(genphoton_category == 1)") )
]
