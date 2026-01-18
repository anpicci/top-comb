""" Definitions to be used in the TOP-23-002 input """
from CMGRDF import Define
from CMGRDF.collectionUtils import DefineSkimmedCollection, DefineP4
from CMGRDF.plots import Plot
from CMGRDF.flow import Cut

evaluate_function = lambda func, args: f"{func}({','.join(args)})"

def define_leptons_partonLevel():
    sequence = [
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
    ]
    return sequence

def define_tops_partonLevel():
    sequence = [
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
    ]
    return sequence

def define_extrajet_partonLevel():
    sequence = [
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
    ]

    return sequence

def define_isolated_photons_particleLevel():

    sequence = [
        Define(
            "is_fiducial_photon_particle_level",
            evaluate_function(
                "isFiducialPhoton_ParticleLevel",
                [
                    "GenIsolatedPhoton_pt",
                    "GenIsolatedPhoton_eta",
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
        DefineP4("FiducialPhoton_particleLevel"),
    ]
    return sequence

def define_dressed_leptons_particleLevel():
    sequence = [
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
        DefineP4("FiducialLepton_particleLevel"),
    ]
    return sequence

def define_jets_particleLevel():
    sequence = [
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
    ]
    return sequence

def define_bjets_particleLevel():

    sequence = [
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
    ] 
    return sequence


def define_other_variables():
    sequence = [
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
    ]
    return sequence


