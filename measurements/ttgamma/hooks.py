# Define hooks for the ttG analysis
from CMGRDF.modifiers import Append, Insert, Prepend
from CMGRDF.flow import Cut
from CMGRDF import Define, AddWeight
from CMGRDF.collectionUtils import DefineSkimmedCollection

evaluate_function = lambda func, args: f"{func}({','.join(args)})"

main_hooks = [
    Prepend( 
        [
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
                eras=[]
            ),
            DefineSkimmedCollection( 
                "FiducialPhoton_partonLevel", 
                "GenPart", 
                mask="is_fiducial_photon_parton_level", 
                members=( 
                    "pt", 
                    "eta", 
                    "phi", 
                    "mass", 
                    "genPartIdxMother", 
                    "pdgId", 
                    "status", 
                    "statusFlags"
                ), 
                optMembers=[]
            ),
            Define( 
                "genphoton_category", 
                evaluate_function( 
                    "get_genphoton_category", 
                    [ 
                        "GenPart_pdgId", 
                        "GenPart_genPartIdxMother", 
                        "GenPart_status", 
                        "GenPart_pt", 
                        "is_fiducial_photon_parton_level" 
                    ]
                ), 
                eras=[]
            )
        ]
    )
]

# From production means that either the 5th or 4th bit are equal to 1 (not both): essentially genphoton_category = 16 (2^4) or 8 (2^3)
from_decay = main_hooks + [ Append( Cut( "fromDecay", "(genphoton_category == 1)" ) ) ]
from_prod = main_hooks + [ Append( Cut( "fromProduction", "genphoton_category == 2 || genphoton_category == 4" ) ) ]




