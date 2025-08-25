/*
This plugin encodes the functionalities to reproduce the fiducial selection used in TOP-23-002.

Author: Carlos Vico (carlos.vico.villalba@cern.ch)
	with the help of Beatriz Ribeiro Lopes
Last updated: 13-08-2025
*/

#include <ROOT/RVec.hxx>

void printHello() {
  // Always implement this function...
  std::cout << " -------------- Hello, you are loading functionalities from TOP-23-002  -------------- " << std::endl;
}

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
	auto mask_origin = ( abs(gen_part_pdgId) == 22 & gen_part_status == 1 );
	
	// Basic kinematic requirements
	auto mask_pt = ( gen_part_pt > 20.0 );
	auto mask_eta = ( abs(gen_part_eta) < 2.5 );

	auto photon_mask = mask_origin & (mask_pt & mask_eta);

	// Make sure this photon has not been produced in ISR/FSR
	for (int i = 0; i < photon_mask.size(); ++i) {
		// Get the genealogic tree for this genPhoton
		// std::cout << photon_mask[ i ] << std::endl;

		bool selected_photon = photon_mask[i];
		if (selected_photon) {
			auto genealogic_tree = get_genealogic_tree( i, gen_part_pdgId, gen_part_idx_mother ); 

			// Now veto the photon if it has a mother that is not a hadron or proton
		    auto mask_tree = Any( !(genealogic_tree < 37 | genealogic_tree == 2212) );
			if (mask_tree)
				
				// Turn off the selection for this photon
			    photon_mask[i] = false;	
				
				// std::cout << "The tree for this photon has a mother with pdgID > 37" << std::endl;
				// for (int j = 0; j < genealogic_tree.size(); j++) {
				// 	std::cout << "    Mother: " << j << " is" << genealogic_tree[ j ] << std::endl;
				// } 
		}
		// std::cout << " ---------------------------- End photon " << i << std::endl;
	} 
	// std::cout << " ---------------------------- " << std::endl;
	//
	
	// Now look for closeby leptons
	auto is_relevant_lep = ( (gen_part_pt > 5.0) & (gen_part_status == 1) & ( abs(gen_part_pdgId) == 11 | abs(gen_part_pdgId) == 13 | abs(gen_part_pdgId) == 15 ) );
	auto selected_leptons_eta = gen_part_eta[ is_relevant_lep ]; 
	auto selected_leptons_phi = gen_part_phi[ is_relevant_lep ]; 

	// Do the same with other particles. Do not include photons or neutrinos 
	auto is_relevant_part = ( (gen_part_pt > 5.0) & (gen_part_status == 1) & (abs(gen_part_pdgId) != 12) & (abs(gen_part_pdgId) != 14) & (abs(gen_part_pdgId) != 16) & (abs(gen_part_pdgId) != 22) );
	auto selected_parts_eta = gen_part_eta[ is_relevant_part ];
	auto selected_parts_phi = gen_part_phi[ is_relevant_part ]; 

	// Clean with dR = 0.1
	auto has_lep_close = cleanByDR_bestMatch( 
		gen_part_eta,
		gen_part_phi,
		selected_leptons_eta,
		selected_leptons_phi,
		0.1
	); 

	// Clean with dR = 0.1
	auto has_part_close = cleanByDR_bestMatch( 
		gen_part_eta,
		gen_part_phi,
		selected_parts_eta,
		selected_parts_phi,
		0.1
	);

	// Get the total mask
	auto is_genphoton = (photon_mask & !(has_lep_close) & !(has_part_close) );

	return is_genphoton;
}

ROOT::RVec<bool> isFiducialPhoton_ParticleLevel(
	const ROOT::RVec<float>& gen_isolated_photon_pt,
	const ROOT::RVec<float>& gen_isolated_photon_eta,
	const ROOT::RVec<int>& gen_isolatedPhoton_lep_dR
	) {
	// Routine to implement fiducial definition of isolated photons
	
	// Basic photon requirements
	auto mask_pt = ( gen_isolated_photon_pt > 20.0 );
	auto mask_eta = ( abs(gen_isolated_photon_eta) < 2.5 );

	auto is_fiducial = (
		mask_pt & mask_eta & gen_isolatedPhoton_lep_dR
	);
	return is_fiducial;
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
	auto mask_final_state_lepton = ( abs(gen_part_pdgId) == 13 | abs(gen_part_pdgId) == 11 ) & (gen_part_status == 1);

	auto is_fiducial = (
		mask_pt & mask_eta & mask_final_state_lepton
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
