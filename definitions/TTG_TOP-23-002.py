""" Definitions to be used in the TOP-23-002 input """
from CMGRDF import Define
from CMGRDF.collectionUtils import DefineSkimmedCollection
from CMGRDF.plots import Plot

evaluate_function = lambda func, args: f"{func}({','.join(args)})"

sequence = [
    # Basic fiducial lepton definition

    # ---- Photons
    Define(
        "is_fiducial_photon",
        evaluate_function(
            "isFiducialGenPhoton",
            [
                "GenPart_pdgId",
                "GenPart_status",
                "GenPart_pt",
                "GenPart_eta",
                "GenPart_genPartIdxMother"
            ],
        ),
        eras=[],
    ),
    DefineSkimmedCollection(
        "FiducialPhoton",
        "GenPart",
        mask="is_fiducial_photon",
        members=(
            "pt",
            "eta",
            "phi",
            "mass"
        ),
        optMembers=[],
    ),

    # ---- Isolated Photons
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
        "is_fiducial_isolated_photon",
        evaluate_function(
            "isFiducialGenIsolatedPhoton",
            [
                "GenIsolatedPhoton_pt",
                "abs(GenIsolatedPhoton_eta)",
                "gen_isolatedPhoton_lep_dR"
            ],
        ),
        eras=[],
    ),
    DefineSkimmedCollection(
        "FiducialIsolatedPhoton",
        "GenIsolatedPhoton",
        mask="is_fiducial_isolated_photon",
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
        "gen_isolatedphoton_pt",
        f"FiducialIsolatedPhoton_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "Leading #gamma #it{p}_{T}",
        legend = "TR",
        unit = "GeV"
    ),
    Plot(
        "genphoton_pt",
        f"FiducialPhoton_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "Leading #gamma #it{p}_{T}",
        legend = "TR",
        unit = "GeV"
    )

]
