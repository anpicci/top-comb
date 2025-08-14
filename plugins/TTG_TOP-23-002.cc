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




