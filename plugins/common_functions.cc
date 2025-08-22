#include <ROOT/RVec.hxx>

ROOT::RVec<int> cleanByDR_bestMatch(
    const ROOT::RVec<float> &coll1_eta,
    const ROOT::RVec<float> &coll1_phi,
    const ROOT::RVec<float> &coll2_eta,
    const ROOT::RVec<float> &coll2_phi,
    float minDR
) {
    unsigned int ncoll1s = coll1_eta.size();
    unsigned int ncoll2s = coll2_eta.size();
    float minDR2 = minDR * minDR;
    ROOT::RVec<int> mask(ncoll1s, 1);
    int jbest = 99;

    for (unsigned i = 0; i < ncoll2s; i++) {

        for (unsigned j = 0; j < ncoll1s; j++) {
            auto dR2 = deltaR2(
                coll2_eta[i], coll2_phi[i],
                coll1_eta[j], coll1_phi[j]
            );

            if (dR2 < minDR2) {
                jbest = j;
                minDR2 = dR2;
            }
        }
    }

    if (jbest != 99)
        mask[jbest] = 0;

    return mask;
}


ROOT::RVec<int> get_genealogic_tree (
    int idx,
    const ROOT::RVec<int>& gen_part_pdgId,
    const ROOT::RVec<int>& gen_part_idx_mother
) {
	// This function takes as an input a particle's index within the GenPart collection.
	// Then recursively tracks its history by iterating over the parents.
	
	ROOT::RVec<int> genealogic_tree; // Not nice since it's size is undeclared...
 
    while (idx >= 0) { // -1 = no mother
		
		// Get the mother
        int mother_idx = gen_part_idx_mother[ idx ];

        if (mother_idx < 0) break; // This particle initiated the chain of decays 


		// If not, there is a mother: save it for tracking the history.
        int mother_pdg = std::abs( gen_part_pdgId[mother_idx] );
		genealogic_tree.push_back( mother_pdg );

        // Move one step up the ancestry chain
        idx = mother_idx;
    }
    return genealogic_tree;
}
