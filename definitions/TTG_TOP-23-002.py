""" Definitions to be used in the TOP-23-002 input """
from CMGRDF import Define
from CMGRDF.collectionUtils import DefineSkimmedCollection, DefineP4
from CMGRDF.plots import Plot
from CMGRDF.flow import Cut

evaluate_function = lambda func, args: f"{func}({','.join(args)})"

sequence = [
    # * ------- PARTON LEVEL ------- * #
    # ---- Photons: defined as a hook. See hooks/TTG_TOP-23-002_photonFromProd.py and hooks/TTG_TOP-002_photonFromDec.py

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
            "mass",
            "genPartIdxMother",
            #"iso",
            "pdgId",
            "status",
            "statusFlags"
        ),
        optMembers=[],
    ),
    DefineP4("FiducialLepton_partonLevel"),

    # ---- TOPs 
    Define(
        "is_top",
        evaluate_function(
            "isTop",
            [
                "GenPart_statusFlags",
                "GenPart_pdgId",
                "GenPart_genPartIdxMother"
            ],
        ),
        eras=[],
    ),
    DefineSkimmedCollection(
        "genTop",
        "GenPart",
        mask="is_top",
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

    DefineP4("genTop"),

    # ---- Extrajet  
    Define(
        "is_genextrajet",
        evaluate_function(
            "isGenExtraJet",
            [
                "GenPart_statusFlags",
                "GenPart_pdgId",
                "GenPart_genPartIdxMother"
            ],
        ),
        eras=[],
    ),
    DefineSkimmedCollection(
        "genExtraJet",
        "GenPart",
        mask="is_genextrajet",
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


    # * ------- PARTICLE LEVEL ------- * #
    # ---- Isolated Photons
    # This function returns True if there are no matches
    # i.e.the photon is clean.
    Define(
        "is_fiducial_photon_particle_level",
        evaluate_function(
            "isFiducialPhoton_ParticleLevel",
            [
                "GenIsolatedPhoton_pt",
                "abs(GenIsolatedPhoton_eta)",
                "GenIsolatedPhoton_phi",
                "GenDressedLepton_eta",
                "GenDressedLepton_phi"
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
            "mass",
            "hasTauAnc",
            "pdgId",
        ),
        optMembers=[],
    ),

    # ---- Jets
    Define(
        "is_fiducial_jet_particle_level",
        evaluate_function(
            "isFiducialJet_ParticleLevel",
            [
                "GenJet_pt",
                "GenJet_eta",
                "GenJet_phi",
                "FiducialLepton_particleLevel_eta",
                "FiducialLepton_particleLevel_phi",
                "FiducialPhoton_particleLevel_eta",
                "FiducialPhoton_particleLevel_phi"
            ],
        ),
        eras=[],
    ),
    DefineSkimmedCollection(
        "FiducialJet_particleLevel",
        "GenJet",
        mask="is_fiducial_jet_particle_level",
        members=(
            "pt",
            "eta",
            "phi",
            "mass",
            "hadronFlavour",
            #"nBHadrons",
            #"nCHadrons",
            "partonFlavour",
        ),
        optMembers=[],
    ),

    # ---- B Jets (Based on fiducial jets!)
    Define(
        "is_fiducial_bjet_particle_level",
        evaluate_function(
            "isFiducialBJet_ParticleLevel",
            [
                "FiducialJet_particleLevel_hadronFlavour",
            ],
        ),
        eras=[],
    ),
    DefineSkimmedCollection(
        "FiducialBJet_particleLevel",
        "FiducialJet_particleLevel",
        mask="is_fiducial_bjet_particle_level",
        members=(
            "pt",
            "eta",
            "phi",
            "mass",
            "hadronFlavour",
            #"nBHadrons",
            #"nCHadrons",
            "partonFlavour",
        ),
        optMembers=[],
    ),

    ## Define variables
    Define(
        "genll_deltaphi",
        evaluate_function(
            "genllDeltaPhi",
            ["FiducialLepton_particleLevel_phi"]
        )
    ),

    ## Define fiducial selection cuts
    Cut( "atleast2genlep", "nFiducialLepton_partonLevel >= 2"),
    Cut( "mll", "(FiducialLepton_partonLevel_p4[0] + FiducialLepton_partonLevel_p4[1]).M() > 30"),
    
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
    ),
    Plot(
        "genjet_pt_particleLevel",
        f"FiducialJet_particleLevel_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "Leading jet #it{p}_{T}",
        legend = "TR",
        unit = "GeV"
    ),
    Plot(
        "genbjet_pt_particleLevel",
        f"FiducialBJet_particleLevel_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "Leading B jet #it{p}_{T}",
        legend = "TR",
        unit = "GeV"
    ),
    Plot(
        "gentop_pt",
        f"genTop_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "Leading top #it{p}_{T}",
        legend = "TR",
        unit = "GeV"
    ),
    Plot(
        "genextrajet_pt",
        f"genExtraJet_pt[ 0 ]",
        (20, 25, 200),
        xTitle = "Leading extrajet #it{p}_{T}",
        legend = "TR",
        unit = "GeV"
    ),
    Plot(
        "genphoton_cat",
        f"genphoton_category",
        (3, 0, 2),
        xTitle = "Photon category",
        legend = "TR",
        unit = "GeV"
    ),
    Plot(
        "genll_deltaphi",
        "genll_deltaphi",
        (10, -3.14, 3.14),
        xTitle = "Lepton #Delta #phi",
        legend = "TR",
        unit = "GeV"
    )
]
