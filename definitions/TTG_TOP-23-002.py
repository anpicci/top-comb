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
        "FiducialTop_partonLevel",
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

    DefineP4("FiducialTop_partonLevel"),

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

    Define(
        "deltaR_pho_closestTop",
        evaluate_function(
            "genDR_photon_closestTop",
            [
                "FiducialPhoton_partonLevel_phi",
                "FiducialPhoton_partonLevel_eta",
                "FiducialTop_partonLevel_phi",
                "FiducialTop_partonLevel_eta"
            ]
        )
    ),

    ## Define fiducial selection cuts
    Cut( "atleast2genlep", "nFiducialLepton_partonLevel >= 2"),
    Cut( "mll", "(FiducialLepton_partonLevel_p4[0] + FiducialLepton_partonLevel_p4[1]).M() > 30"),
    
]


# Custom spams for the plot below
cat_spams = {
    "spam1": { "text": "Bits", "x0": 0.65, "y0": 0.64, "x1": 0.975, "y1": 0.67, "textsize": 22 },
    "spam2": { "text": "1st: from lepton", "x0": 0.65, "y0": 0.58, "x1": 0.975, "y1": 0.61, "textsize": 22 },
    "spam3": { "text": "2nd: from w or b", "x0": 0.65, "y0": 0.49, "x1": 0.975, "y1": 0.52, "textsize": 22 },
    "spam4": { "text": "3rd: from top decay", "x0": 0.65, "y0": 0.43, "x1": 0.975, "y1": 0.46, "textsize": 22 },
    "spam5": { "text": "4rd: from ISR", "x0": 0.65, "y0": 0.37, "x1": 0.975, "y1": 0.40, "textsize": 22 },
    "spam6": { "text": "5th: from top prod", "x0": 0.65, "y0": 0.31, "x1": 0.975, "y1": 0.34, "textsize": 22 },
}
bin_bitlabels = ["00000","00001","00010","00011","00100","00101","00110","00111","01000","01001","01010","01011","01100","01101","01110","01111","10000","10001","10010","10011","10100","10101","10110","10111","11000","11001","11010","11011","11100","11101","11110","11111"]

plots = {
    # This variable takes 2**5 possibilities
    "genphoton_categories" : Plot( "genphoton_categories", f"genphoton_category", (32, 0, 32), xTitle = "Generator level photon categories (parton level)", legend = "TR", unit = "", xBinLabels = bin_bitlabels, do_superwide = True, verticalLabels = True, logy = False, custom_spams = cat_spams ),
    "leading_genphoton_pt" : Plot( "leading_genphoton_pt", f"FiducialPhoton_partonLevel_pt[0]", (10, 20, 140), xTitle = r"Generator level #it{p}_{T} (#gamma)", legend = "TR", unit = "GeV" ),
    "deltaR_pho_closestTop" : Plot( "deltaR_pho_closestTop", f"deltaR_pho_closestTop", (14, 0, 5), xTitle = r"Generator level #Delta R (#gamma, closest top)", legend = "TR", unit = "" ),
}
