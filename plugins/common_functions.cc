#include <ROOT/RVec.hxx>

ROOT::RVec<int> get_parents_pdgId(
    const ROOT::RVec<int>& pdgIds,
    const ROOT::RVec<int>& motherIdx,
    const ROOT::RVec<int>& startIdx,
    int N
) {

	// The return should be the same size as the original list
	// Note that level 0 returns the first parents!
	// Level 1 returns the grandparents
	// and so on...
    ROOT::RVec<int> parents_pdgIds(startIdx.size(), 0);

    for (int i = 0; i < startIdx.size(); i++) {
        int idx = startIdx[i];

        // climb N generations up
        for (int level = 0; level < N; level++) {
            if ( idx < 0 || idx >= motherIdx.size() ) {
                idx = -1; // no ancestor
                break;
            }
			// Keep updating the idx until we reach the desired level of parenting
            idx = motherIdx[idx];
        }

        if (idx >= 0 && idx < pdgIds.size()) { 
			parents_pdgIds[i] = pdgIds[idx];
        } else {
            parents_pdgIds[i] = 0; // no valid ancestor
        }
    }

    return parents_pdgIds;
}



ROOT::RVec<int> get_genealogic_tree (
    int seed_idx,
    const ROOT::RVec<int>& pdgIds,
    const ROOT::RVec<int>& motherIdx
) {
	// This function takes as an input a particle's index within the GenPart collection.
	// Then recursively tracks its history by iterating over the parents.
	// 
	// This function could be vectorized, but probably there's not much to gain.
	int idx = seed_idx;
	ROOT::RVec<int> genealogic_tree; // Not nice since it's size is undeclared...
    while (idx >= 0) { // -1 = no mother
		
		// Get the mother
        int mother_idx = motherIdx[ idx ];

        if (mother_idx < 0) break; // This particle initiated the chain of decays 

		// If not, there is a mother: save it for tracking the history.
        int mother_pdg = pdgIds[mother_idx];
		genealogic_tree.push_back( mother_pdg );

        // Move one step up the ancestry chain
        idx = mother_idx;
    }

    return genealogic_tree;
}



