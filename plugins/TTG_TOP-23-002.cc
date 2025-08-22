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

ROOT::RVec<bool> isFiducialLepton( 
		const ROOT::RVec<float>& gen_lep_pt 
    ) {

    // Function to Define what a loose lepton is in the WZ analysis

    // common
    auto mask = ( gen_lep_pt > 10 ); 
    return mask; 
}

ROOT::RVec<bool> isFiducialGenPhoton(
	const ROOT::RVec<int>& gen_part_pdgId,
	const ROOT::RVec<int>& gen_part_status,
	const ROOT::RVec<int>& gen_part_pt,
	const ROOT::RVec<int>& gen_part_abseta,
	const ROOT::RVec<int>& gen_part_idx_mother
	) {
	// Routine to implement fiducial definition of photons
	
 	// Select generator level photons with stable PYTHIA status
	auto mask_origin = ( gen_part_pdgId == 22 & gen_part_status == 1 );
	
	// Basic kinematic requirements
	auto mask_pt = ( gen_part_pt > 20.0 );
	auto mask_eta = ( abs(gen_part_abseta) < 2.5 );

	// Make sure this photon has not been produced in ISR/FSR
	auto mask_mother = (
		gen_part_idx_mother < 37 // Not a hadron
	);

	// Get the list of gen photons
	auto gen_photon_pdgId = gen_part_pdgId[ mask_origin ];
	auto gen_photon_pdgId_v2 = gen_part_pdgId[ mask_origin & (mask_pt & mask_eta) ];
	std::cout << "There are: " << gen_part_pdgId.size() << " particles" << std::endl;
	std::cout << "There are: " << gen_photon_pdgId.size() << " photons" << std::endl;
	std::cout << "There are: " << gen_photon_pdgId.size() << " photons with pT > 20 and |eta| < 2.5" << std::endl;
	std::cout << " ---------------------------- " << std::endl;
	
	//for (int i = 0; gen_part_pdgId.size(); ++i) {
	//	// Get the genealogic tree for this genPhoton
	//	std::cout << "GenPhoton pdgId: " << gen_photon_pdgId[ i ] << std::endl; 
	//} 

	return mask_origin;
}

ROOT::RVec<bool> isFiducialGenIsolatedPhoton(
	const ROOT::RVec<float>& gen_isolated_photon_pt,
	const ROOT::RVec<float>& gen_isolated_photon_abseta,
	const ROOT::RVec<int>& gen_isolatedPhoton_lep_dR
	) {
	// Routine to implement fiducial definition of isolated photons
	
	// Basic photon requirements
	auto mask_pt = ( gen_isolated_photon_pt > 20.0 );
	auto mask_eta = ( abs(gen_isolated_photon_abseta) < 2.5 );

	auto is_fiducial = (
		mask_pt & mask_eta & gen_isolatedPhoton_lep_dR
	);
	return is_fiducial;
}


