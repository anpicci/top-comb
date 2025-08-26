/*
This plugin encodes the functionalities to reproduce the fiducial selection used in TOP-23-002.

Author: Carlos Vico (carlos.vico.villalba@cern.ch)
	with the help of Beatriz Ribeiro Lopes
Last updated: 13-08-2025
*/

#include <ROOT/RVec.hxx>

void printHello() {
  std::cout << " -------------- Hello, you are loading functionalities from TOP-23-002  -------------- " << std::endl;
}

/* PARTON LEVEL FUNCTIONS */
ROOT::RVec<bool> isFiducialPhoton_PartonLevel(
	const ROOT::RVec<int>& gen_part_pdgId,
	const ROOT::RVec<int>& gen_part_status,
	const ROOT::RVec<int>& gen_part_pt,
	const ROOT::RVec<int>& gen_part_eta,
	const ROOT::RVec<int>& gen_part_phi,
	const ROOT::RVec<int>& gen_part_idx_mother
	) {
	// Routine to implement fiducial definition of photons
	
 	// Select generator level photons with stable PYTHIA status
	auto mask_origin = ( (abs(gen_part_pdgId) == 22) & (gen_part_status == 1 ) );
	
	// Basic kinematic requirements
	auto mask_pt = ( gen_part_pt > 20.0 );
	auto mask_eta = ( abs(gen_part_eta) < 2.5 );

	auto photon_mask = mask_origin & (mask_pt & mask_eta);

	// Make sure this photon has not been produced in ISR/FSR
	for (int i = 0; i < photon_mask.size(); ++i) {
		// Get the genealogic tree for this genPhoton
		bool selected_photon = photon_mask[i];
		if (selected_photon) {
			auto genealogic_tree = get_genealogic_tree( gen_part_idx_mother[i], gen_part_pdgId, gen_part_idx_mother ); 

			// Now veto the photon if it has a mother that is a hadron (excluding the proton)
		    auto has_hadron_ancestor = Any( (genealogic_tree > 37) & (genealogic_tree != 2212) );
			if ( has_hadron_ancestor  )
			    photon_mask[i] = false;	
		}
	} 

	// Now look for closeby leptons
	auto is_relevant_lep = ( (gen_part_pt > 5.0) & (gen_part_status == 1) & ( (abs(gen_part_pdgId) == 11) | (abs(gen_part_pdgId) == 13) | (abs(gen_part_pdgId) == 15) ) );
	auto selected_leptons_eta = gen_part_eta[ is_relevant_lep ]; 
	auto selected_leptons_phi = gen_part_phi[ is_relevant_lep ]; 

	// Do the same with other particles. Do not include photons or neutrinos 
	auto is_relevant_part = ( (gen_part_pt > 5.0) & (gen_part_status == 1) & (abs(gen_part_pdgId) != 12) & (abs(gen_part_pdgId) != 14) & (abs(gen_part_pdgId) != 16) & (abs(gen_part_pdgId) != 22) );
	auto selected_parts_eta = gen_part_eta[ is_relevant_part ];
	auto selected_parts_phi = gen_part_phi[ is_relevant_part ]; 

	// Clean with dR = 0.1
	auto isolated_from_lep = cleanByDR( 
		gen_part_eta,
		gen_part_phi,
		selected_leptons_eta,
		selected_leptons_phi,
		0.1
	); 

	// Clean with dR = 0.1
	auto isolated_from_parton = cleanByDR( 
		gen_part_eta,
		gen_part_phi,
		selected_parts_eta,
		selected_parts_phi,
		0.1
	);

	// Get the total mask
	auto is_genphoton = ( photon_mask & isolated_from_lep & isolated_from_parton );
	return is_genphoton;

}



ROOT::RVec<bool> isFiducialLepton_PartonLevel(
	const ROOT::RVec<int>& gen_part_pdgId,
	const ROOT::RVec<int>& gen_part_status,
	const ROOT::RVec<float>& gen_part_pt,
	const ROOT::RVec<float>& gen_part_eta
	) {
	// Routine to implement fiducial definition of isolated photons
	
	// Basic photon requirements
	auto mask_pt = ( gen_part_pt > 5.0 );
	auto mask_eta = ( abs(gen_part_eta) < 2.5 );
	auto mask_final_state_lepton = ( (abs(gen_part_pdgId) == 13) | ( abs(gen_part_pdgId) == 11 ) & ( gen_part_status == 1 ) );

	auto is_fiducial = (
		mask_pt & mask_eta & mask_final_state_lepton
	);
	return is_fiducial;
}

ROOT::RVec<bool> isTop(
	const ROOT::RVec<int>& gen_part_statusFlags,
	const ROOT::RVec<int>& gen_part_pdgId,
	const ROOT::RVec<int>& gen_part_idx_mother
	) {

	// Routine to implement fiducial definition of isolated photons
	auto is_last_copy = ( ( gen_part_statusFlags & (1 << 13) ) != 0 );
	auto is_valid_top = ( ( abs( gen_part_pdgId ) == 6 ) & ( gen_part_idx_mother > 0 ) );

	auto is_fiducial = ( is_last_copy & is_valid_top );
	return is_fiducial;
}

ROOT::RVec<bool> isGenExtraJet(
    const ROOT::RVec<int>& gen_part_statusFlags,
    const ROOT::RVec<int>& gen_part_pdgId,
    const ROOT::RVec<int>& gen_part_idx_mother
    ) {

    // Routine to implement fiducial definition of isolated photons
    auto is_valid_bottom = abs( gen_part_pdgId ) == 5;
    auto is_first_copy = ( (gen_part_statusFlags & (1 << 12) ) != 0 );
	auto mother_pdgId = get_parents_pdgId( gen_part_pdgId, gen_part_idx_mother, gen_part_idx_mother, 0 );

    auto is_fiducial = ( is_first_copy & is_valid_bottom & ( abs(mother_pdgId) == 6 ) );
    return is_fiducial;
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

int get_genphoton_category(
	const ROOT::RVec<int>& genpart_pdgId,
	const ROOT::RVec<int>& genpart_motherIdx,
	const ROOT::RVec<int>& genpho_pdgId,
	const ROOT::RVec<int>& genpho_statusFlags,
	const ROOT::RVec<int>& genpho_motherIdx
	) {
	// Create boolean masks to tag the origin of the photon
	if (genpho_pdgId.empty()) return 0;  // no photons
	auto is_first_copy = ( (genpho_statusFlags & ( 1 << 12 )) != 0 ); // First copy

	auto mothers_pdgId = get_parents_pdgId( genpart_pdgId, genpart_motherIdx, genpho_motherIdx, 0 );
	auto grandmothers_pdgId = get_parents_pdgId( genpart_pdgId, genpart_motherIdx, genpho_motherIdx, 1 );

	auto mother_is_lepton = ( ( abs(mothers_pdgId) == 11 ) | ( abs(mothers_pdgId) == 13 ) | ( abs(mothers_pdgId) == 15 ) );
	auto mother_is_w_or_b = ( ( abs(mothers_pdgId) == 24 ) | ( abs(mothers_pdgId) == 5 ) );
	auto mother_is_top = ( abs(mothers_pdgId) == 6 ); 
	//auto mother_is_w = ( abs(mothers_pdgId) == 24 );
	//auto mother_is_b = ( abs(mothers_pdgId) == 5 ); 
	//auto mother_is_gluon = ( abs(mothers_pdgId) == 21 ); 

	// The photon is not considered as coming from the top if it does not
	// have a top in the chain.
	ROOT::RVec<bool> not_from_top = ROOT::RVec<bool>( genpho_pdgId.size(), true );

	for (int ipho = 0; ipho < genpho_pdgId.size(); ipho++) {
		int motherIdx = genpho_motherIdx[ ipho ];	
	    auto tree = get_genealogic_tree(
	        motherIdx,
	        genpart_pdgId,
	        genpart_motherIdx
	    );

	    if ( Any( abs(tree) == 6 ) ) not_from_top[ipho] = false;
	}
	
    auto is_top_decay = ( mother_is_top & ( grandmothers_pdgId == mothers_pdgId) ); // Targets photon emitted from top leg
	
	auto is_from_decay = ( // Targets photon attached to lepton, b or top. 
		is_first_copy & (
			( mother_is_lepton ) | 
			( !not_from_top & mother_is_w_or_b ) | 
			( is_top_decay ) 
		)
	);

	//auto is_from_decay_lep = ( mother_is_lepton ); // Attached to a lepton
	//auto is_from_decay_wb = ( (!not_from_top) & (mother_is_w_or_b) ); // Attached to a W or b quark (top decay products)
	//auto is_from_decay_w = ( (!not_from_top) & (mother_is_w) ); // Attached to a W 
	//auto is_from_decay_b = ( (!not_from_top) & (mother_is_b) ); // Attached to a b quark
	//auto is_from_decay_top = ( is_top_decay ); // Attached to the top

	//auto is_top_prod = ( ((mother_is_top) & (!is_top_decay)) | mother_is_gluon );  // This includes ISR (madgraph sets mother to gluon for ISR photons)
	//auto is_isr_prod = ( ((!mother_is_top) & (!is_top_decay)) & (!mother_is_gluon) ) // This includes ISR from quarks;

	// Now define categories based on the origin of the **leading** photon.
	return is_from_decay[0] ? 1 : 2; // 1 = from decay, 2 = not from decay
}
