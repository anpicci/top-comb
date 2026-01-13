/*
This plugin encodes the functionalities to reproduce the fiducial selection used in TOP-23-002.

Author: Carlos Vico (carlos.vico.villalba@cern.ch)
    with the help of Beatriz Ribeiro Lopes
Last updated: 06-12-2025
*/
#include <ROOT/RVec.hxx>
#include "functions.h"
#include "eft_auxiliars.h"

ROOT::RVec<bool> isFiducialPhoton_PartonLevel(
    const ROOT::RVec<int>& pdgId,
    const ROOT::RVec<int>& status,
    const ROOT::RVec<float>& pt,
    const ROOT::RVec<float>& eta,
    const ROOT::RVec<float>& phi,
    const ROOT::RVec<int>& idx_mother
    ) {
    /**
     * Identifies fiducial photons at the parton level.
     * -------------------------------------------------------------------------------- 
     * Applies the fiducial selection criteria defined in TOP-23-002:
     * - Requires stable PYTHIA status (status == 1)
     * - Applies kinematic acceptance cuts: pT > 20 GeV, |eta| < 2.5
     * - Enforces isolation from leptons (dR > 0.4)
     * - Enforces isolation from other stable particles excluding neutrinos (dR > 0.4)
     * - Vetoes photons originating from hadrons (excluding protons)
     * -------------------------------------------------------------------------------- 
     */

    log( 0, " -------------------- " );
    log( 0, "Identifying fiducial level photons..." );
    // Select generator level photons with stable PYTHIA status
    auto photon_mask = ( 
        ( abs(pdgId) == 22 ) & // Photon pdgId
        ( status == 1 ) & // PYTHIA8 stable status
        ( (pt > 20.0) & ( abs(eta) < 2.5 ) ) // Acceptance
    );

    log( 1, " Initial mask applied: status = 1, pt > 20.0, abs(eta) < 2.5. Left with %d photon candidates", (int) photon_mask[ photon_mask == 1 ].size() );

    // Signal photons will be required to be isolated from these leptons
    auto is_relevant_lep = ( 
        (pt > 5.0) & // Minimum pT 
        (status == 1) & // Stable particles
        // Must be isolated from any kind of lepton
        ( 
            (abs(pdgId) == 11) | 
            (abs(pdgId) == 13) | 
            (abs(pdgId) == 15) 
        ) 
    );
    auto selected_leptons_eta = eta[ is_relevant_lep ]; 
    auto selected_leptons_phi = phi[ is_relevant_lep ]; 

    // Do the same with other particles except neutrinos and other photons. 
    auto is_relevant_part = ( 
        ( pt > 5.0 ) & 
        ( status == 1 ) & 
        ( abs(pdgId) != 12 ) & 
        ( abs(pdgId) != 14 ) & 
        ( abs(pdgId) != 16 ) & 
        ( abs(pdgId) != 22 ) 
    );
    auto selected_parts_eta = eta[ is_relevant_part ];
    auto selected_parts_phi = phi[ is_relevant_part ]; 

    auto isolated_from_lep = cleanByDR( 
        eta,
        phi,
        selected_leptons_eta,
        selected_leptons_phi,
        0.4
    );

    auto isolated_from_part = cleanByDR( 
        eta,
        phi,
        selected_parts_eta,
        selected_parts_phi,
        0.4
    );

    photon_mask = ( photon_mask & ( isolated_from_lep ) & ( isolated_from_part ) );

    // Now for each photon, check:
    //  - History: must not be originated from a hadron (not including proton)
    //  - Isolation from relevant particles defined above.
    for (int i = 0; i < (int)photon_mask.size(); ++i) {
        bool selected_photon = photon_mask[i];
        if (selected_photon) {

            log( 2, " Checking out photon %d", i );

            // Track the history of this particle and get the pdgId.
            auto genealogic_tree = get_all_ancestors_properties( 
                idx_mother[i], // Seed particle to start tracking
                idx_mother, // List of mother IDX to track
                pdgId // Property that we want to get for each ancestor
            ); 

            // Now veto the photon if it has a mother that is a hadron (excluding the proton)
            auto has_hadron_ancestor = Any( 
                ( abs(genealogic_tree) > 37 ) & 
                ( abs(genealogic_tree) != 2212) 
            );

            if ( has_hadron_ancestor ) {
                log(3, "There is a hadron (not-proton, 2212) ancestor for this photon. This photon is not selected." );
                log(3, "List of ancestors:" );
                loglist(4, genealogic_tree );
                photon_mask[i] = false;
            }
        }
    } 

    auto is_genphoton = ( photon_mask );
    log(2, "Number of fiducial photons: %d.", is_genphoton[ is_genphoton == 1 ].size() );
    return is_genphoton; 
}



ROOT::RVec<bool> isFiducialLepton_PartonLevel(
    const ROOT::RVec<int>& pdgId,
    const ROOT::RVec<int>& status,
    const ROOT::RVec<float>& pt,
    const ROOT::RVec<float>& eta
    ) {

    /**
    * Identifies fiducial leptons at the parton level.
    * 
    * Applies the fiducial selection criteria defined in TOP-23-002:
    * - Requires electrons (pdgId = 11) or muons (pdgId = 13)
    * - Requires stable PYTHIA status (status == 1)
    * - Applies kinematic acceptance cuts: pT > 5 GeV, |eta| < 2.5
    */
    
    auto is_fiducial = (
        ( pt > 5.0 ) & 
        ( abs(eta) < 2.5 ) & 
        ( status == 1 ) &
        ( 
            ( abs(pdgId) == 13 ) | ( abs(pdgId) == 11 ) 
        ) 
    );

    return is_fiducial;
}


ROOT::RVec<bool> isTop(
    const ROOT::RVec<int>& statusFlags,
    const ROOT::RVec<int>& pdgId,
    const ROOT::RVec<int>& mother_idx
    ) {
    /**
     * Identifies top quarks at the parton level.
     * 
     * Selects top quarks that pass fiducial criteria defined in TOP-23-002:
     * - Requires pdgId = 6 (top quark)
     * - Requires last copy status flag (statusFlags bit 13)
     * - Requires presence of a parent particle (mother_idx > 0)
     * 
     * Note: The last copy status ensures we select the final-state top quark
     * before it decays, avoiding duplicates from the parton shower.
     */
    auto is_fiducial = ( 
        ( ( statusFlags & (1 << 13) ) != 0 ) &  // Get the last copy 
        ( abs( pdgId ) == 6 ) & // Must be a top... 
        ( mother_idx > 0 ) // Must have a parent 
    );
    return is_fiducial;
}


ROOT::RVec<bool> isGenExtraJet(
    const ROOT::RVec<int>& statusFlags,
    const ROOT::RVec<int>& pdgId,
    const ROOT::RVec<int>& idx_mother
    ) {

    /**
    * Identifies b-jets from top decays at the parton level.
    * 
    * Selects b-quarks that come from top quark decays:
    * - Requires pdgId = 5 (b-quark)
    * - Requires isFromHardProcess status flag (statusFlags bit 12)
    * - Requires mother particle to be a top quark (pdgId = 6)
    * 
    * These b-jets are used to characterize extra jets from the top decay chain.
    */

    auto mother_pdgId = get_parents_properties( 
        idx_mother, 
        idx_mother, 
        pdgId, // Property that we want to obtain 
        0 
    );

    auto is_fiducial = ( 
        ( (statusFlags & (1 << 12 ) ) != 0 ) & 
        ( abs( pdgId ) == 5 ) & 
        ( abs( mother_pdgId ) == 6 ) 
    );
    return is_fiducial;
}



int get_genphoton_category(
    const ROOT::RVec<int>& pdgId,
    const ROOT::RVec<int>& motherIdx,
    const ROOT::RVec<int>& status,
    const ROOT::RVec<float>& pt,
    const ROOT::RVec<bool>& is_fiducial_photon_parton_level
    ) {

    /**
     * Categorizes generator-level photons by their production mechanism.
     * 
     * This function characterizes fiducial parton-level photons based on their origin:
     * - **Decay photons**: Originate from decay chains (lepton decays, W/b decays, top decays)
     * - **ISR photons**: Initial state radiation photons not from top production
     * - **Offshell top photons**: Photons from offshell top quarks or their radiations
     * 
     * The categorization is based on the leading (highest pT) photon.
     * Returns a bitmask where:
     *   - Bit 0: Photon from any decay process
     *   - Bit 1: Photon from ISR production
     *   - Bit 2: Photon from offshell top production
     */

    log( 0, "Categorizing sample based on generator level photons..." );
    log( 1, "Getting first copies" );
    ROOT::RVec<bool> is_valid_first_copy = get_first_copy(
        pdgId, // List of all genParticle pdgIds
        motherIdx, // List of all genParticle motherIdx
        is_fiducial_photon_parton_level
    );
    log( 1, "First copy has been selected" );
    auto photon_pdgId = pdgId[ is_valid_first_copy ];
    auto photon_motherIdx = motherIdx[ is_valid_first_copy ];

    auto mothers_pdgId  = get_parents_properties( 
        photon_motherIdx, 
        motherIdx, 
        pdgId, 
        0 
    );

    auto grandmothers_pdgId  = get_parents_properties( 
        photon_motherIdx, 
        motherIdx, 
        pdgId, 
        1 
    );


    log( 1, "Checking ancestors for the first copy" );
    auto mother_is_lepton = ( ( abs(mothers_pdgId) == 11 ) | ( abs(mothers_pdgId) == 13 ) | ( abs(mothers_pdgId) == 15 ) );
    auto mother_is_w_or_b = ( ( abs(mothers_pdgId) == 24 ) | ( abs(mothers_pdgId) == 5 ) );
    auto mother_is_top    = ( abs(mothers_pdgId) == 6 ); 
    auto mother_is_offshel_t = ( abs(mothers_pdgId) == 21 ); 

    // The photon is not considered as coming from the top if it does not
    // have a top in the chain.
    ROOT::RVec<bool> not_from_top = ROOT::RVec<bool>( photon_pdgId.size(), true );
    for (int ipho = 0; ipho < (int)photon_pdgId.size(); ipho++) {
        auto ancestors_pdgIds = get_all_ancestors_properties(
            photon_motherIdx[ ipho ],
            motherIdx,
            pdgId
        );
        not_from_top[ipho] = !( Any( abs( ancestors_pdgIds ) == 6 ) );
    }

    // Use cases
    // From decay categories:
    auto is_top_decay = ( (mother_is_top) & ( grandmothers_pdgId == mothers_pdgId ) ); 
   
 
    auto is_from_lepton_decay = ( mother_is_lepton );
    auto is_from_wb_decay = ( (!not_from_top) & (mother_is_w_or_b) );
    auto is_from_top_decay = ( is_top_decay );
    auto is_from_decay = ( is_from_lepton_decay | is_from_wb_decay | is_from_top_decay );

    auto is_from_isr_production        = ( ( (!mother_is_top) & (!is_from_decay) ) & (!mother_is_offshel_t) );
    auto is_from_offshell_t_production = ( ( ( mother_is_top) & (!is_from_decay) ) | mother_is_offshel_t );
    auto is_from_production = ( is_from_isr_production | is_from_offshell_t_production );

    // Now define categories based on the origin of the **leading** photon.

    // Get the index of the highest pt photon
    int lead_pho_idx = 0;
    auto photon_pt = pt[ is_valid_first_copy ];
    for ( int ipho = 0; ipho < (int) photon_pt.size(); ipho++ ) {
        if ( photon_pt[ipho] > photon_pt[lead_pho_idx] ) {
            lead_pho_idx = ipho;
        }
    }
    log( 1, "Pts: ");
    loglist( 2, photon_pt );
    log( 2, "Leading photon index: %d ", lead_pho_idx);

    int category = 0;
    category |= is_from_decay[lead_pho_idx] << 0; // Bit for ANY decay
    category |= is_from_isr_production[lead_pho_idx] << 1; // Bit for ISR production
    category |= is_from_offshell_t_production[lead_pho_idx] << 2; // Bit for OFFSHELL top production

    log( 1, "Are photons from lepton decay?" );
    loglist( 2, is_from_lepton_decay );
    log( 1, "Are photons from w/b decay?" );
    loglist( 2, is_from_wb_decay );
    log( 1, "Are photons from top decay?" );
    loglist( 2, is_from_wb_decay );
    log( 1, "Are photons from decay (overall)?" );
    loglist( 2, is_from_decay );
    log( 1, "Are photons from ISR?" );
    loglist( 2, is_from_isr_production );
    log( 1, "Are photons from top production?" );
    loglist( 2, is_from_offshell_t_production );
    log( 1, "Final category: %d", category );

    return category;
}


/* PARTICLE LEVEL FUNCTIONS */


ROOT::RVec<bool> isFiducialPhoton_ParticleLevel(
    const ROOT::RVec<float>& gen_isolated_photon_pt,
    const ROOT::RVec<float>& gen_isolated_photon_eta,
    const ROOT::RVec<float>& gen_isolated_photon_phi,
    const ROOT::RVec<float>& gen_dressed_lepton_eta,
    const ROOT::RVec<float>& gen_dressed_lepton_phi
    ) {
    
    /**
    * Identifies fiducial photons at the particle level.
    * 
    * Applies the particle-level fiducial selection defined in TOP-23-002:
    * - Selects isolated photons provided by generator
    * - Applies kinematic cuts: pT > 20 GeV, |eta| < 2.5
    * - Enforces isolation from dressed leptons (dR > 0.1)
    */
    
    // Basic photon requirements
    auto mask_pt = ( gen_isolated_photon_pt > 20.0 );
    auto mask_eta = ( abs(gen_isolated_photon_eta) < 2.5 );

    // Clean with dR = 0.1
    // This function returns 0 on the isolated photon
    // position which has a lepton closeby.
    auto isolated_from_lep = cleanByDR( 
        gen_isolated_photon_eta,
        gen_isolated_photon_phi,
        gen_dressed_lepton_eta,
        gen_dressed_lepton_phi,
        0.1
    );

    auto is_fiducial = (
        mask_pt & mask_eta & ( isolated_from_lep != 0 )
    );
    return is_fiducial;
}


ROOT::RVec<bool> isFiducialLepton_ParticleLevel(
    const ROOT::RVec<float>& gen_dressed_lepton_pt,
    const ROOT::RVec<float>& gen_dressed_lepton_eta
    ) {

    /**
    * Identifies fiducial leptons at the particle level.
    * 
    * Applies the particle-level fiducial selection defined in TOP-23-002:
    * - Selects dressed leptons (QED-corrected) provided by generator
    * - Applies kinematic cuts: pT > 15 GeV, |eta| < 2.5
    */

    auto mask_pt = ( gen_dressed_lepton_pt > 15.0 );
    auto mask_eta = ( abs(gen_dressed_lepton_eta) < 2.5 );

    auto is_fiducial = (
        mask_pt & mask_eta 
    );

    return is_fiducial;
}


ROOT::RVec<bool> isFiducialJet_ParticleLevel(
    const ROOT::RVec<float>& gen_jet_pt,
    const ROOT::RVec<float>& gen_jet_eta,
    const ROOT::RVec<float>& gen_jet_phi,
    const ROOT::RVec<float>& gen_dressed_lepton_eta,
    const ROOT::RVec<float>& gen_dressed_lepton_phi,
    const ROOT::RVec<float>& gen_isolated_photon_eta,
    const ROOT::RVec<float>& gen_isolated_photon_phi
    ) {

    /**
    * Identifies fiducial jets at the particle level.
    * 
    * Applies the particle-level fiducial selection defined in TOP-23-002:
    * - Applies kinematic cuts: pT > 30 GeV, |eta| < 2.4
    * - Enforces isolation from dressed leptons (dR > 0.4)
    * - Enforces isolation from isolated photons (dR > 0.4)
    * 
    * The particle-level jets are built from stable final-state particles 
    * by the generator and represent experimentally observable jets.
    * 
    */

    auto mask_pt = ( gen_jet_pt > 30.0 );
    auto mask_eta = ( abs(gen_jet_eta) < 2.4 );

    auto isolated_from_lep = cleanByDR( 
        gen_jet_eta,
        gen_jet_phi,
        gen_dressed_lepton_eta,
        gen_dressed_lepton_phi,
        0.4
    );

    auto isolated_from_pho = cleanByDR( 
        gen_jet_eta,
        gen_jet_phi,
        gen_isolated_photon_eta,
        gen_isolated_photon_phi,
        0.4
    );

    auto is_fiducial = (
        mask_pt & mask_eta & ( isolated_from_lep != 0) & ( isolated_from_pho != 0)
    );

    return is_fiducial;
}


ROOT::RVec<bool> isFiducialBJet_ParticleLevel(
    const ROOT::RVec<int>& fiducial_genjet_hadronFlavour
    ) {
    
    /**
    * Identifies b-tagged jets at the particle level.
    * 
    * Selects jets that have been identified as containing b-hadrons 
    * by the generator's hadron flavor classification.
    * 
    * This function should typically be applied after isFiducialJet_ParticleLevel()
    * to get b-jets that pass the full fiducial selection.
    */
    
    auto is_fiducial = (
        fiducial_genjet_hadronFlavour == 5 
    );

    return is_fiducial;
}