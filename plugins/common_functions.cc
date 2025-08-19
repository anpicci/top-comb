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

