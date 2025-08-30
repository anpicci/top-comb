/*
 * Common functions that may be useful for different analyses.
 * author: Carlos Vico (carlos.vico.villalba@cern.ch)
 */

#include <ROOT/RVec.hxx>

ROOT::RVec<int> get_parents_properties( const ROOT::RVec<int>& startIdx, const ROOT::RVec<int>& motherIdx, const ROOT::RVec<int>& input_properties, int N ); 
ROOT::RVec<int> get_all_ancestors_properties ( const int seed_idx, const ROOT::RVec<int>& parentIdx, const ROOT::RVec<int>& input_properties );
ROOT::RVec<float> get_all_ancestors_properties ( const int seed_idx, const ROOT::RVec<int>& parentIdx, const ROOT::RVec<float>& input_properties );

