/*
 * Common functions that may be useful for different analyses.
 * author: Carlos Vico (carlos.vico.villalba@cern.ch)
 */

#include "common_functions.h" 

ROOT::RVec<int> get_parents_properties(
    const ROOT::RVec<int>& startIdx,
    const ROOT::RVec<int>& motherIdx,
    const ROOT::RVec<int>& input_properties,
    int N ) {

    /*
    * This function climbs up the ladder tracking 
    * the ancestors of a given particle, then returns
    * the desired property for that particular ancestor.
    */

    ROOT::RVec<int> parents_properties(startIdx.size(), 0);
    for (int i = 0; i < (int)startIdx.size(); i++) {
        int idx = startIdx[i];
    
        // climb N generations up
        for (int level = 0; level < N; level++) {
            // Keep updating the idx until we reach the desired level of parenting
            idx = motherIdx[idx];
        }
    
        if (idx >= 0 ) { 
         parents_properties[i] = input_properties[idx];
        } else {
            parents_properties[i] = 0; // no valid ancestor
        }
    }
   
    return parents_properties;
}

ROOT::RVec<int> get_all_ancestors_properties (
    const int seed_idx,
    const ROOT::RVec<int>& parentIdx,
    const ROOT::RVec<int>& input_properties
) {

    /*
    * This function tracks the history of a given
    * GenPart, and returns a vector with the properties
    * as provided by the second argument.
    *
    * Essentially this returns a vector with the size
    * equal to the number of ancestors. Each component
    * of the returned vector is a given input_properties of the
    * ancestor (e.g. pdgId, status, statusFlags, etc...)
    *
    * Use the overloaded method to get floating values
    */

    int idx = seed_idx;
    ROOT::RVec<int> properties; 

    while (idx >= 0) { // -1 = no parent
     	properties.push_back( input_properties[ idx ] );
        idx = parentIdx[idx]; // Look for the next parent
    }

    return properties;
}

ROOT::RVec<float> get_all_ancestors_properties (
    const int seed_idx,
    const ROOT::RVec<int>& parentIdx,
    const ROOT::RVec<float>& input_properties
) {

    /*
    * This function is equal to the method
    * overloaded with <int>, just for <floating>
    * values.
    *
    * It can be used to get e.g. the pT of each
    * ancestor of a given particle.
    */

    int idx = seed_idx;
    ROOT::RVec<float> properties; 

    while (idx >= 0) { // -1 = no parent
     	properties.push_back( input_properties[ idx ] );
        idx = parentIdx[idx]; // Look for the next parent
    }

    return properties;
}
