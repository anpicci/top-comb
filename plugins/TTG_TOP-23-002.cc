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

ROOT::RVec<bool> isFiducialPhoton(
	const ROOT::RVec<float>& gen_isolated_photon_pt,
	const ROOT::RVec<float>& gen_isolated_photon_abseta,
	const ROOT::RVec<int>& gen_isolatedPhoton_lep_dR
	) {
	// Routine to implement fiducial definition of photons
	
	// Basic photon requirements
	auto mask_pt = ( gen_isolated_photon_pt > 20.0 );
	auto mask_eta = ( gen_isolated_photon_abseta < 2.5 );

	auto is_fiducial = (
		mask_pt & mask_eta & gen_isolatedPhoton_lep_dR
	);
	return is_fiducial;
}


