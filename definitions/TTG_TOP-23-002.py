""" Definitions to be used in the TOP-23-002 input """
from CMGRDF import Define
from CMGRDF.collectionUtils import DefineSkimmedCollection
from CMGRDF.plots import Plot

evaluate_function = lambda func, args: f"{func}({','.join(args)})"

sequence = [
    # Basic fiducial lepton definition

    # * ------- PARTON LEVEL ------- * #
    # ---- Photons
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
    ),
    DefineSkimmedCollection(
        "FiducialPhoton_partonLevel",
        "GenPart",
        mask="is_fiducial_photon_parton_level",
        members=(
            "pt",
            "eta",
            "phi",
            "mass"
        ),
        optMembers=[],
    ),

    # ---- Leptons
    Define(
        "is_fiducial_lepton_parton_level",
        evaluate_function(
            "isFiducialLepton_PartonLevel",
            [
                "GenPart_pdgId",
                "GenPart_status",
                "GenPart_pt",
                "GenPart_eta",
            ],
        ),
        eras=[],
    ),
    DefineSkimmedCollection(
        "FiducialLepton_partonLevel",
        "GenPart",
        mask="is_fiducial_lepton_parton_level",
        members=(
            "pt",
            "eta",
            "phi",
            "mass"
        ),
        optMembers=[],
    ),


    # * ------- PARTICLE LEVEL ------- * #
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
        "is_fiducial_photon_particle_level",
        evaluate_function(
            "isFiducialPhoton_ParticleLevel",
            [
                "GenIsolatedPhoton_pt",
                "abs(GenIsolatedPhoton_eta)",
                "gen_isolatedPhoton_lep_dR"
            ],
        ),
        eras=[],
    ),
    DefineSkimmedCollection(
        "FiducialPhoton_particleLevel",
        "GenIsolatedPhoton",
        mask="is_fiducial_photon_particle_level",
        members=(
            "pt",
            "eta",
            "phi",
            "mass"
        ),
        optMembers=[],
    ),

    # ---- Dressed Leptons
    Define(
        "is_fiducial_lepton_particle_level",
        evaluate_function(
            "isFiducialLepton_ParticleLevel",
            [
                "GenDressedLepton_pt",
                "GenDressedLepton_eta",
            ],
        ),
        eras=[],
    ),
    DefineSkimmedCollection(
        "FiducialLepton_particleLevel",
        "GenDressedLepton",
        mask="is_fiducial_lepton_particle_level",
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
        "genphoton_pt_particleLevel",
        f"FiducialPhoton_particleLevel_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "Leading ISO #gamma #it{p}_{T}",
        legend = "TR",
        unit = "GeV"
    ),

    Plot(
        "genphoton_pt_partonLevel",
        f"FiducialPhoton_partonLevel_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "Leading #gamma #it{p}_{T}",
        legend = "TR",
        unit = "GeV"
    ),

    Plot(
        "genlepton_pt_partonLevel",
        f"FiducialLepton_partonLevel_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "Leading lepton #it{p}_{T}",
        legend = "TR",
        unit = "GeV"
    ),

    Plot(
        "genlepton_pt_particleLevel",
        f"FiducialLepton_particleLevel_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "Leading dressed lepton #it{p}_{T}",
        legend = "TR",
        unit = "GeV"
    )

]
