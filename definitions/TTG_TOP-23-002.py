""" Definitions to be used in the TOP-23-002 input """
from CMGRDF import Define
from CMGRDF.collectionUtils import DefineSkimmedCollection
from CMGRDF.plots import Plot

evaluate_function = lambda func, args: f"{func}({','.join(args)})"

print(evaluate_function(
            "cleanByDR_bestMatch",
            [
                "GenIsolatedPhoton_eta",
                "GenIsolatedPhoton_phi",
                "GenDressedLepton_eta",
                "GenDressedLepton_phi",
                "0.4"
            ]
        )
)
sequence = [
    # Basic fiducial lepton definition

    # ---- Photons
    # This function returns True if there are no matches
    # i.e.the photon is clean.
    Define( 
        "gen_isolatedPhoton_lep_dR",
        evaluate_function(
            "cleanByDR_bestMatch",
            [
                "GenIsolatedPhoton_eta",
                "GenIsolatedPhoton_phi",
                "GenDressedLepton_eta",
                "GenDressedLepton_phi",
                "0.4"
            ]
        )
    ),
    Define(
        "is_fiducial_photon",
        evaluate_function(
            "isFiducialPhoton",
            [
                "GenIsolatedPhoton_pt",
                "abs(GenIsolatedPhoton_eta)",
                "gen_isolatedPhoton_lep_dR"
            ],
        ),
        eras=[],
    ),
    DefineSkimmedCollection(
        "FiducialPhoton",
        "GenIsolatedPhoton",
        mask="is_fiducial_photon",
        members=(
            "pt",
            "eta",
            "phi",
            "mass"
        ),
        optMembers=[],
    ),
]



plots = [

    Plot(
        "genphoton_pt",
        f"FiducialPhoton_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "Leading #gamma #it{p}_{T}",
        legend = "TR",
        unit = "GeV"
    )

]
