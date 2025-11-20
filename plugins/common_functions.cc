/*
 * Common functions that may be useful for different analyses.
 * author: Carlos Vico (carlos.vico.villalba@cern.ch)
 */
#include <stdio.h>
#include "common_functions.h" 

ROOT::RVec<bool> get_first_copy(
    const ROOT::RVec<int> pdgId,
    const ROOT::RVec<int> motherIdx,
    const ROOT::RVec<bool> filter
    )   {

    /*
    This function returns the indices of the GenPart list that are associated with particles
    that are first in the production chain. 
    */

    ROOT::RVec<bool> is_first_copy = ROOT::RVec<bool>( pdgId.size(), false ); 
    
    // Iterate over all genParticles, but only analyze those that are fiducial photons.
    for (int ipart = 0; ipart < (int)pdgId.size(); ipart++) {

        if ( (!filter[ipart]) ) { continue; } 
        log( 2, "Searching for the first copy of particle with idx: %d", ipart );
        auto pdgId_target = pdgId[ipart]; 
        
        // Now we want to find the position, within the GenPart list, for
        // the first copy of the photon. 
        auto ancestors_motherIdx = get_all_ancestors_properties(
            ipart, // Here the seed is the particle itself, as we want to fetch the first parent also
            motherIdx, // Complete list of GenPart mothers
            motherIdx // We want to return the motherIdx.
        );

        auto ancestors_pdgId = get_all_ancestors_properties(
            motherIdx[ipart], 
            motherIdx, // Complete list of GenPart mothers
            pdgId // We want to return the motherIdx.
        );

        int first_copy_idx = ipart; // Assume that the particle is already the first copy

        log( 3, "List of ancestors:" );
        loglist( 4, ancestors_pdgId );
        for ( auto& ancestor_idx : ancestors_motherIdx ) {
            // If the ancestor has the same pdgId, then it means the previous one
            // was not the first copy, so update.
            if ( abs( pdgId[ ancestor_idx ] ) == pdgId_target ) {
                log( 4, "Particle with idx: %d set to first copy", ancestor_idx );
                first_copy_idx = ancestor_idx; 
            }
        }

        // By now we should have found the first copy
        is_first_copy[ first_copy_idx ] = true; 
    }

    return is_first_copy;
}