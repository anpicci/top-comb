/*
This plugin encodes the functionalities to reproduce the fiducial selection used in TOP-23-002.

Author: Carlos Vico (carlos.vico.villalba@cern.ch)
    with the help of Beatriz Ribeiro Lopes
Last updated: 27-08-2025
*/

#include <ROOT/RVec.hxx>
#include "functions.h"
#include "common_functions.h"


enum Category {
    FromLeptonDecay        = 1 << 0,  // 00001
    FromWBDecay            = 1 << 1,  // 00010
    FromTopDecay           = 1 << 2,  // 00100
    FromISRProduction      = 1 << 3,  // 01000
    FromOffshellTProduction= 1 << 4   // 10000
};

/* PARTON LEVEL FUNCTIONS */
ROOT::RVec<bool> isFiducialPhoton_PartonLevel(
    const ROOT::RVec<int>& pdgId,
    const ROOT::RVec<int>& status,
    const ROOT::RVec<float>& pt,
    const ROOT::RVec<float>& eta,
    const ROOT::RVec<float>& phi,
    const ROOT::RVec<int>& idx_mother
    ) {

    /*
     * This function is used to implement the fiducial definition
     * for PHOTONS at the PARTON LEVEL. The routine has been
     * implemented in a way that mimics what is done in TOP-23-002.
     */
    
    // Select generator level photons with stable PYTHIA status
    auto photon_mask = ( 
        ( abs(pdgId) == 22 ) & // Photon pdgId
        ( status == 1 ) & // PYTHIA8 stable status
        ( (pt > 20.0) & ( abs(eta) < 2.5 ) ) // Acceptance
    );


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


    // Now for each photon, check:
    //  - History: must not be originated from a hadron (not including proton)
    //  - Isolation from relevant particles defined above.
    for (int i = 0; i < (int)photon_mask.size(); ++i) {
        bool selected_photon = photon_mask[i];
        if (selected_photon) {

            // Check if the photon is isolated from other leptons
            auto deltaR2_pho_lep = deltaR2( 
                eta[i], // Photon eta 
                phi[i], // Photon phi
                selected_leptons_eta, // Lepton eta
                selected_leptons_phi  // Lepton phi
            );

            // Check if the photon is isolated from other particles
            auto deltaR2_pho_part = deltaR2( 
                eta[i], // Photon eta 
                phi[i], // Photon phi
                selected_parts_eta, // Lepton eta
                selected_parts_phi  // Lepton phi
            );

            // The photon is not isolated if there's at least one particle within 
            // a cone of 0.1.
            if ( Any( deltaR2_pho_lep < 0.1 ) ) photon_mask[i] = false; 
            if ( Any( deltaR2_pho_part < 0.1 ) ) photon_mask[i] = false; 

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

            photon_mask[i] = !(has_hadron_ancestor); // True if there's no hadron ancestor 
                                                     // that is not a proton 
        }
    } 

    auto is_genphoton = ( photon_mask );
    return is_genphoton; 
}



ROOT::RVec<bool> isFiducialLepton_PartonLevel(
    const ROOT::RVec<int>& pdgId,
    const ROOT::RVec<int>& status,
    const ROOT::RVec<float>& pt,
    const ROOT::RVec<float>& eta
    ) {

    /*
     * This function is used to implement the fiducial definition
     * for LEPTONS at the PARTON LEVEL. The routine has been
     * implemented in a way that mimics what is done in TOP-23-002.
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
    /*
     * This function is used to implement the fiducial definition
     * for TOP QUARKS at the PARTON LEVEL. The routine has been
     * implemented in a way that mimics what is done in TOP-23-002.
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

    /*
     * This function is used to implement the fiducial definition
     * for B JETS FROM THE TOP at the PARTON LEVEL. The routine has been
     * implemented in a way that mimics what is done in TOP-23-002.
     */

    auto mother_pdgId = get_parents_properties( 
        idx_mother, 
        idx_mother, 
        pdgId, // Property that we want to obtain 
        0 
    );

    auto is_fiducial = ( 
        ( (statusFlags & (1 << 12) ) != 0 ) & 
        ( abs( pdgId ) == 5 ) & 
        ( abs( mother_pdgId ) == 6 ) 
    );
    return is_fiducial;
}

int get_genphoton_category(
    const ROOT::RVec<int>& pdgId,
    const ROOT::RVec<int>& motherIdx,
    const ROOT::RVec<int>& status,
    const ROOT::RVec<bool>& is_fiducial_photon_parton_level
    ) {

    /*
     * This function is used to characterize PHOTONS defined
     * at the PARTON LEVEL. It basically tags the origin based on:
     *  - Last copy of the photon
     *  - A photon is considered from production only if it comes from ISR 
     */


    // ---------------------------------------------------------------------------
    // 1. Consider the first copies of the fiducial photons. The original code
    // used in TTG-23-002 did not make use of the GenPart_statusFlags branch
    // of the nanoAOD, so we manually replicate the behaviour here. 
    // ---------------------------------------------------------------------------
    // 
    // # Few things have been changed for better readibility, just variable naming.
    // def get_first_copy(genpart):
    //    first_copy = genpart
    //
    //    # Loop until the frame is filled with the first copy of each particle
    //    # in the dataframe, for a given event.
    //
    //    while not ak.all( ak.all( first_copy.parent.pdgId != first_copy.pdgId, axis=1 ) ):
    //        first_copy = ak.where(
    //          first_copy.parent.pdgId == first_copy.pdgId,
    //          first_copy.parent,
    //          first_copy
    //        )
    //    return first_copy
    //
    // ---------------------------------------------------------------------------
    

    ROOT::RVec<bool> is_first_copy = ROOT::RVec<bool>( pdgId.size(), false ); 

    #ifdef _DEBUGCOMB
    std::cout << " >> Getting first copy photon... " << " Iterating over " << pdgId.size() << " particles." << std::endl;
    #endif

    // Iterate over all genParticles, but only analyze those that are fiducial photons.
    for (int ipart = 0; ipart < (int)pdgId.size(); ipart++) {

        if ( !is_fiducial_photon_parton_level[ ipart ] ) continue;

        // Now we want to find the position, within the GenPart list, for
        // the first copy of the photon. 
        auto ancestors_motherIdx = get_all_ancestors_properties(
            ipart, // Here the seed is the particle itself, as we want to fetch the first parent also
            motherIdx, // Complete list of GenPart mothers
            motherIdx // We want to return the motherIdx.
        );

        int first_copy_idx = ipart; // Assume that the particle is already the first copy

        #ifdef _DEBUGCOMB
        std::cout << "   - Particle " << first_copy_idx 
                << " is a fiducial photon. Proof: pdgId:"  << pdgId[ipart] 
                << " with valid mask:" << is_fiducial_photon_parton_level[ipart] << 
        std::endl;
        std::cout << "   - Will now check if it is the first copy" << std::endl; 

        auto ancestors_pdgIds = get_all_ancestors_properties(
            motherIdx[ ipart ], // First mother of the photon
            motherIdx, // Complete list of GenPart mothers
            pdgId // We want to return the motherIdx.
        );
        
        std::cout << "   - Ancestors: "; 
        for ( auto& ancestor_pdgid : ancestors_pdgIds ) { std::cout << ancestor_pdgid << ","; }
        std::cout << "" << std::endl; 
        #endif

        for ( auto& ancestor_idx : ancestors_motherIdx ) {
            // If the ancestor is a photon, then it means the previous one
            // was not the first copy, so update.
            #ifdef _DEBUGCOMB
            std::cout << "    - Checking ancestor  " << ancestor_idx << " which has pdgId: " << pdgId[ ancestor_idx ] << std::endl;
            #endif 

            if ( abs( pdgId[ ancestor_idx ] ) == 22 ) {
                #ifdef _DEBUGCOMB
                std::cout << "     + There's an ancestor with pdgId 22. So the first copy is updated to " << ancestor_idx << std::endl;
                #endif 
                first_copy_idx = ancestor_idx; 
            }
            
        }

        // By now we should have found the first copy
        #ifdef _DEBUGCOMB
        std::cout << "     + Setting " << first_copy_idx << " particle as first copy!" << std::endl;
        #endif 

        is_first_copy[ first_copy_idx ] = true;
      
    }

    auto photon_pdgId = pdgId[ is_first_copy ];
    auto photon_motherIdx = motherIdx[ is_first_copy ];

    if (photon_pdgId.empty()) return 0;  // no photons

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

    #ifdef _DEBUGCOMB
    auto wbfromtop = ( (!not_from_top) & (mother_is_w_or_b) );
    std::cout  << "Leading photon Mother is lepton? " << mother_is_lepton[0] << std::endl;
    std::cout  << "Leading photon Mother is W or b from top branch? " << wbfromtop[0] << std::endl;
    std::cout  << "Leading photon Mother is top decay? " << is_top_decay[0] << std::endl;
    std::cout  << "Conclusion: is decay? " << is_from_decay[0] << std::endl;
    std::cout  << "----------------------" << is_from_decay[0] << std::endl;
    #endif

    int category = 0;

    category |= is_from_lepton_decay[0] << 0; // Bit for lepton decay 
    category |= is_from_wb_decay[0] << 1; // Bit for W or b decay
    category |= is_from_top_decay[0] << 2; // Bit for top decay
    category |= is_from_decay[0] << 2; // Bit for ANY decay
    category |= is_from_isr_production[0] << 3; // Bit for ISR production
    category |= is_from_offshell_t_production[0] << 4; // Bit for OFFSHELL top production

    // Now define categories based on the origin of the **leading** photon.
    //return ( is_from_decay[0] ) ? 1 : 2; // 1 = from decay, 2 = not from decay
    return category;
}

// Specific ttG variables
float genllDeltaPhi( 
    const ROOT::RVec<float>& fiducial_genlep_phi
) {
    if ( (int)fiducial_genlep_phi.size() < 2 ) { return -99; }

    float genll_deltaphi = deltaPhi( fiducial_genlep_phi[0], fiducial_genlep_phi[1] );
    
    return genll_deltaphi;
}

float genDR_photon_closestTop(
    const ROOT::RVec<float>& photon_phi, 
    const ROOT::RVec<float>& photon_eta, 
    const ROOT::RVec<float>& top_phi, 
    const ROOT::RVec<float>& top_eta 
) {
    // Compute the deltaR between the leading photon and the top closest to it.
    float deltaR_photon_TOP1 = deltaR2( top_eta[0], top_phi[0], photon_eta[0], photon_phi[0] );
    float deltaR_photon_TOP2 = deltaR2( top_eta[1], top_phi[1], photon_eta[0], photon_phi[0] );
    
    float minDeltaR2 = std::min( deltaR_photon_TOP1, deltaR_photon_TOP2 );
    float minDeltaR = std::sqrt( minDeltaR2 );
    return minDeltaR;  
}


/* PARTICLE LEVEL FUNCTIONS */
ROOT::RVec<bool> isFiducialPhoton_ParticleLevel(
    const ROOT::RVec<float>& gen_isolated_photon_pt,
    const ROOT::RVec<float>& gen_isolated_photon_eta,
    const ROOT::RVec<float>& gen_isolated_photon_phi,
    const ROOT::RVec<float>& gen_dressed_lepton_eta,
    const ROOT::RVec<float>& gen_dressed_lepton_phi
    ) {
    // Routine to implement fiducial definition of isolated photons
    
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
    // Routine to implement fiducial definition of isolated photons
    
    // Basic photon requirements
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
    // Routine to implement fiducial definition of isolated photons
    
    // Basic photon requirements
    auto mask_pt = ( gen_jet_pt > 30.0 );
    auto mask_eta = ( abs(gen_jet_eta) < 2.5 );

    auto isolated_from_lep = cleanByDR( 
        gen_jet_pt,
        gen_jet_phi,
        gen_dressed_lepton_eta,
        gen_dressed_lepton_phi,
        0.4
    );

    auto isolated_from_pho = cleanByDR( 
        gen_jet_pt,
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
    // Routine to implement fiducial definition of isolated photons
    auto is_fiducial = (
        fiducial_genjet_hadronFlavour == 5 
    );

    return is_fiducial;
}


