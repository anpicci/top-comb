# This file illustrates how to implement a processor, realizing the selection
# steps and outputting histograms and a cutflow with efficiencies.

import pepper
import numpy as np
# from coffea.analysis_objects import JaggedCandidateArray as Jca
from functools import partial
from collections import namedtuple
import uproot
import awkward as ak
import logging
from copy import copy
from helpers import cut_defs
from helpers import col_defs
from pepper.processor_basic import ProcessorBasicPhysics 
from pepper.scale_factors import ScaleFactors
#from pepper.config_basic import ConfigBasicPhysics
import json

#use this instead of basic config because of photon and PSV scale factors
class ConfigTTGamma(pepper.ConfigBasicPhysics):
    def __init__(self, path_or_file, textparser=json.load, cwd="."):
        """Initialize the configuration.

        Arguments:
        path_or_file -- Either a path to the file containing the configuration
                        or a file-like object of it
        textparser -- Callable to be used to parse the text contained in
                      path_or_file
        cwd -- A path to use as the working directory for relative paths in the
               config. The actual working directory of the process might change
        """
        super().__init__(path_or_file, textparser, cwd)
        self.behaviors.update({
            "trigger_sfs":
                self._get_trigger_sfs,
            "hists": self._get_hists,
            "btag_sf16pre": self._get_btag_sf
        })

    def _get_trigger_sfs(self, value):
        path, histnames = value
        ret = {}
        if len(histnames) != 3:
            raise pepper.config.ConfigError(
                "Need 3 histograms for trigger scale factors. Got "
                f"{len(histnames)}")
        with uproot.open(self._get_path(path)) as f:
            for chn, histname in zip(("ee", "em", "mm"), histnames):
                ret[chn] = ScaleFactors.from_hist(
                    f[histname], dimlabels=["lep1_pt", "lep2_pt"])
        return ret
    
# The following means = VariationArg = ("VariationArgs":
# ["name", "junc"=None, "jer"=central, "met"=central] )
VariationArg = namedtuple(
    "VariationArgs", ["name", "junc", "jer", "met", "hem"],
    defaults=(None, "central", "central", None))

logger = logging.getLogger(__name__)

class Processor(ProcessorBasicPhysics):

    config_class = ConfigTTGamma
    
    def __init__(self, config, eventdir):
        
        super().__init__(config, None)

        if "pdf_types" in config:
            self.pdf_types = config["pdf_types"]
        else:
            if config["compute_systematics"]:
                logger.warning(
                    "pdf_type not specified; will not compute pdf "
                    "uncertainties. (Options are 'Hessian', 'MC' and "
                    "'MC_Gaussian')")
            self.pdf_types = None

    def process_selection(self, selector, dsname, is_mc, filler):
        # Implement the selection steps: add cuts, definine objects and/or
        # compute event weights

        era = self.get_era(selector.data, is_mc)
        # Implement the selection steps: add cuts, definine objects and/or
        # compute event weights

        if dsname.startswith("TTTo"):
            selector.set_column("gent_lc", self.gentop, lazy=True)
            if "top_pt_reweighting" in self.config:
                selector.add_cut(
                    "TopPtReweighting", self.do_top_pt_reweighting,
                    no_callback=True)

        #GenPhotons
        if is_mc:
            selector.set_column("GenPart", partial(self.build_genpart_column, is_mc))
            selector.set_column("GenPhoton", self.build_genphoton_column)
            selector.set_column("GenIsolatedPhoton", partial(self.build_genphoton_partlevel_column, is_mc))
            selector.set_column("GenLepton", partial(self.build_genlepton_column, is_mc))
            selector.set_column("GenDressedLepton", partial(self.build_genlepton_partlevel_column, is_mc))
            selector.set_column("GenJet", partial(self.build_genjet_column, is_mc))
            #selector.set_column("GenJet", partial(self.build_genjet_column_theory, is_mc))
            selector.set_column("GenBJet", partial(self.build_genbjet_column, is_mc))
            #selector.set_column("genllDeltaPhi", partial(self.genllDeltaPhi, is_mc))
            selector.set_column("GenTop", self.gentop)
            selector.set_column("GenTopPos", self.gentoppos)
            selector.set_column("GenTopNeg", self.gentopneg)
            selector.set_column("GenExtraJet", partial(self.build_genextrajet_column, is_mc))
            selector.set_column("genNjet", col_defs.n_genjet)
            selector.set_column("genNbjet", col_defs.n_genbjet)

            #variables for cross section
            selector.set_column("genllDeltaPhi", partial(self.genllDeltaPhi, is_mc))
            selector.set_column("genDRphottbar", partial(self.genDRphottbar, is_mc))
            selector.set_column("genDeltaYTops", partial(self.genDeltaYTops, is_mc))
            selector.set_column("genDRphoClosTop", partial(self.genDRphoClosTop, is_mc))
            #selector.set_column("genDRphoClosLep", partial(self.genDRphoClosLep, is_mc))
            selector.set_column("genmttbar", partial(self.genmttbar, is_mc))
            selector.set_column("genmttgamma", partial(self.genmttgamma, is_mc))

        if ("ST_tW_" in dsname) or ("TTTo" in dsname) or ("TTGamma" in dsname):
            selector.set_multiple_columns(self.genphotons_categories)
            selector.add_cut("PhotonFromDecayOrNoPhoton", self.photon_from_decay, no_callback=True) #OrNoPhoton
            
        #from tWgamma ang ttgamma NLO keep only photons from production
        elif ("ST_TWG" in dsname) or ("TTGJets" in dsname):
            selector.set_multiple_columns(self.genphotons_categories)
            selector.add_cut("PhotonFromProduction", self.photon_from_production, no_callback=True)

        diffbins='inclusive'
        if self.config["compute_systematics"] and is_mc:
            #add the generator level uncertainties normalized per bin
            self.add_me_uncertainties(dsname, selector)
            self.add_ps_uncertainties(dsname, selector)
            self.add_pdf_uncertainties(dsname, selector)

        selector.add_cut("PhotonsCategorized", cut_defs.dummycut)
        
        selector.set_cat("ngenphotons",  {'zeropartlevelphotons','exactly1partlevelphoton','zerophotons','exactly1photon'})
        selector.set_multiple_columns(self.ngenphotons)

        selector.add_cut("totalcrossection",self.dummy_cut)

        selector.add_cut("atleast2genlep",self.atleast2genlep)
        selector.set_column("genmll", self.genmass_lepton_pair, no_callback=True, categories={"ngenphotons": ['exactly1photon','zerophotons']})
        selector.add_cut("genmllcut", self.good_mass_genlepton_pair,  categories={"ngenphotons": ['exactly1photon','zerophotons']})
        
        #selector.add_cut("fiducialcrosssection_partonlevel",partial(self.fiducialcrosssection_partonlevel, dsname),categories={"ngenphotons": ['exactly1photon']})
        #selector.add_cut("fiducialcrosssection_partonlevel_nophoton",partial(self.fiducialcrosssection_partonlevel_nophoton, dsname),categories={"ngenphotons": ['zeropartlevelphotons','exactly1partlevelphoton','zerophotons']})

        selector.add_cut("atleast2partlevellep",self.atleast2partlevellep, no_callback=True)
        selector.set_column("genmllPartLevel", self.genmass_lepton_pair_partlevel, no_callback=True)
        selector.add_cut("fiducialcrosssection",partial(self.fiducialcrosssection, dsname))
        #selector.add_cut("exactly2genlep",self.exactly2genlep)
        selector.add_cut("atleast2bjets",partial(self.atleast2bjets, dsname))
            
        logger.debug("Selection done")

    def genllDeltaPhi(self, is_mc, data):

        genLep = data["GenDressedLepton"]

        try:
            genlepton = genLep[ak.argsort(genLep["pt"], ascending=False)]
        except:
            genlepton = genLep

        genlepton = ak.pad_none(genlepton,2,axis=1)

        deltaphi = np.abs(genlepton[:, 0].phi-genlepton[:, 1].phi)
        deltaphi = ak.fill_none(deltaphi,-10.)

        deltaphi = ak.where(deltaphi<np.pi,deltaphi,2*np.pi-deltaphi)

        return deltaphi

    def build_genphoton_column(self, data):

        genphoton = data["GenPart"]

        genphoton = genphoton[genphoton["pdgId"]==22]
        genphoton = genphoton[genphoton["status"]==1]
        # genphoton = genphoton[genphoton.hasFlags('isFirstCopy')]#(genphoton["status"]==1)

        has_pt = (genphoton["pt"]>20)
        has_eta = (abs(genphoton["eta"])<2.5)

        genphoton = genphoton[has_pt & has_eta]

        mother = genphoton.parent

        mother_is_not_hadron = (abs(mother["pdgId"]) < 37)

        while not ak.all(ak.is_none(mother, axis=1)):
            mother_is_not_hadron = (mother_is_not_hadron & ( (ak.fill_none(abs(mother["pdgId"]), 0) < 37) | (ak.fill_none(abs(mother["pdgId"]), 0) == 2212) )) #mother is not hadron, except proton, proton is okay
            mother = mother.parent

        genpart = data["GenPart"]   

        is_relevant_lep = ((genpart["pt"]>5.) & (genpart.status==1) & #(genpart.hasFlags('isFirstCopy')) &
                    ((abs(genpart["pdgId"])==11) | (abs(genpart["pdgId"])==13) | (abs(genpart["pdgId"])==15)))

        relevant_lep = genpart[is_relevant_lep]

        has_lep_close = ak.any(genphoton.metric_table(relevant_lep) < 0.1, axis=2) 

        is_relevant_part = ((genpart["pt"]>5.) &  (genpart.status==1) & #(genpart.hasFlags('isFirstCopy')) & 
                    (abs(genpart["pdgId"])!=12) & (abs(genpart["pdgId"])!=14) & (abs(genpart["pdgId"])!=16) & (abs(genpart["pdgId"])!=22))

        relevant_part = genpart[is_relevant_part]

        has_part_close = ak.any(
            genphoton.metric_table(relevant_part) < 0.1, axis=2) 

        genphoton = genphoton[~has_lep_close & ~has_part_close & mother_is_not_hadron]
        return genphoton

    def build_genphoton_partlevel_column(self, is_mc, data):

        genphoton = data["GenIsolatedPhoton"]
        genlep = data["GenDressedLepton"]
        
        has_pt = genphoton["pt"]>20.
        has_eta = abs(genphoton["eta"])<2.5

        genphoton = genphoton[has_pt & has_eta] 

        has_lep_close = ak.any(
            genphoton.metric_table(genlep) < 0.4, axis=2) 

        genphoton = genphoton[~has_lep_close]
        #sort by pt
        try:
          genphoton = genphoton[ak.argsort(genphoton["pt"], ascending=False)]
        except:
          genphoton = genphoton

        return genphoton

    def build_genlepton_column(self, is_mc, data):

        genlepton = data["GenPart"]

        is_lepton = ( (abs(genlepton["pdgId"])==13) | (abs(genlepton["pdgId"])==11) )
        is_final_state = (genlepton["status"]==1)

        has_pt = genlepton["pt"]>5.
        has_eta = abs(genlepton["eta"])<2.5

        genlepton = genlepton[is_lepton & is_final_state & has_pt & has_eta]

        return genlepton

    def build_genlepton_partlevel_column(self, is_mc, data):

        genlepton = data["GenDressedLepton"]

        has_pt = genlepton["pt"]>15.
        has_eta = abs(genlepton["eta"])<2.5

        genlepton = genlepton[has_pt & has_eta]

        return genlepton

    def build_genjet_column(self, is_mc, data):

        genjet = data["GenJet"]
        genlep = data["GenDressedLepton"]
        genpho = data["GenIsolatedPhoton"]

        has_pt = (genjet["pt"]>30.)
        has_eta = (abs(genjet["eta"])<2.4)

        has_pho_close = ak.any(genjet.metric_table(genpho) < 0.4, axis=2) 
        has_lep_close = ak.any(genjet.metric_table(genlep) < 0.4, axis=2) 

        genjet = genjet[has_pt & has_eta & ~has_lep_close & ~has_pho_close]

        return genjet

    def build_genjet_column_theory(self, is_mc, data):

        genjet = data["GenJet"]
        genlep = data["GenLepton"]
        genpho = data["GenPhoton"]

        has_pt = (genjet["pt"]>30.)
        has_eta = (abs(genjet["eta"])<2.4)

        has_pho_close = ak.any(genjet.metric_table(genpho) < 0.4, axis=2) 
        has_lep_close = ak.any(genjet.metric_table(genlep) < 0.4, axis=2) 

        genjet = genjet[has_pt & has_eta & ~has_lep_close & ~has_pho_close]

        return genjet

    def build_genbjet_column(self, is_mc, data):

        genjet = data["GenJet"]

        is_b = (genjet.hadronFlavour==5)

        genjet = genjet[is_b]

        return genjet


    def build_genextrajet_column(self, is_mc, data):

        genextrajet = data["GenJet"]

        bquark_from_top = data["GenPart"]
        bquark_from_top = bquark_from_top[abs(bquark_from_top.pdgId)==5]
        bquark_from_top = bquark_from_top[bquark_from_top.hasFlags('isFirstCopy')]
        bquark_from_top = bquark_from_top[abs(bquark_from_top.parent.pdgId)==6]

        genextrajet=genextrajet[ak.all(genextrajet.metric_table(bquark_from_top)>0.4,axis=-1)]

        return genextrajet

    """     def build_genbjet_column(self, is_mc, data):

        bjet=data["GenJet"][(data["GenJet"].hadronFlavour)==5]

        bquark_from_top = data["GenPart"]
        bquark_from_top = bquark_from_top[abs(bquark_from_top.pdgId)==5]
        bquark_from_top = bquark_from_top[bquark_from_top.hasFlags('isFirstCopy')]
        bquark_from_top = bquark_from_top[abs(bquark_from_top.parent.pdgId)==6]

        bjet=bjet[ak.any(bjet.metric_table(bquark_from_top)<0.4,axis=-1)]

        return bjet """

    def build_genpart_column(self, is_mc, data):
        genpart = data["GenPart"]

        return genpart

    def gentop(self, data):
        part = data["GenPart"]
        part = part[~ak.is_none(part.parent, axis=1)]
        part = part[part.hasFlags("isLastCopy")]
        part = part[abs(part.pdgId) == 6]
        part = part[ak.argsort(part.pdgId, ascending=False)]
        return part

    def gentoppos(self, data):
        part = data["GenPart"]
        part = part[~ak.is_none(part.parent, axis=1)]
        part = part[part.hasFlags("isLastCopy")]
        part = part[(part.pdgId) == 6]
        return part

    def gentopneg(self, data):
        part = data["GenPart"]
        part = part[~ak.is_none(part.parent, axis=1)]
        part = part[part.hasFlags("isLastCopy")]
        part = part[(part.pdgId) == -6]
        return part

    def dummy_cut(self,data):
        genlep = data["GenPart"]
        accept = (ak.num(genlep) >= 0)
        return accept

    def exactly2genlep(self,data):

        genlep = data["GenLepton"]

        return (ak.num(genlep)==2)

    def atleast2genlep(self,data):

        genlep = data["GenLepton"]

        return (ak.num(genlep)>=2)

    def atleast2partlevellep(self,data):

        genlep = data["GenDressedLepton"]

        return (ak.num(genlep)>=2)

    def fiducialcrosssection(self,dsname,data):

        genpho = data["GenIsolatedPhoton"]
        genlep = data["GenDressedLepton"]
        genjet = data["GenJet"]
        genbjet = data["GenBJet"]

        if "TTTo" in dsname:
            photonmask = ak.where(data["decay"],(ak.num(genpho)==1),(ak.num(genpho)==0))
        else:
            photonmask = (ak.num(genpho)==1)

        return (photonmask & (ak.num(genlep)>=2) & (ak.num(genjet)>=2) & (ak.num(genbjet)>=1) & (data["genmllPartLevel"]>30))

    def fiducialcrosssection_partonlevel(self,dsname,data):

        genpho = data["GenPhoton"]
        genlep = data["GenLepton"]
        genjet = data["GenJet"]
        genbjet = data["GenBJet"]
        genpart = data["GenPart"]

        closeby_part = genpart[(genpart.pdgId!=22) & (genpart.pt>0.5) & (genpart.status==1)]
        distance = closeby_part.metric_table(genpho)
        distance = ak.firsts(distance)
        closeby_part = closeby_part[distance<0.4]

        closeby_part_pt = closeby_part.pt
        closeby_part_pt = ak.pad_none(closeby_part_pt,1)
        closeby_part_pt = ak.fill_none(closeby_part_pt,0)

        ptsum_closebypart=ak.sum(closeby_part_pt,axis=1)
        is_isolated = (ptsum_closebypart<(0.5*ak.firsts(genpho).pt))

        return (is_isolated & (ak.num(genlep)>=2) & (ak.num(genjet)>=2) & (ak.num(genbjet)>=1) & (data["genmll"]>30))

    def fiducialcrosssection_partonlevel_nophoton(self,dsname,data):

        genlep = data["GenLepton"]
        genjet = data["GenJet"]
        genbjet = data["GenBJet"]

        return ((ak.num(genlep)>=2) & (ak.num(genjet)>=2) & (ak.num(genbjet)>=1) & (data["genmll"]>30))

    def atleast2bjets(self,dsname,data):

        #genjet = data["GenJet"]
        genbjet = data["GenBJet"]

        return (ak.num(genbjet)>=2)

    def genphotons_categories(self,data):
        
        genpho = data["GenPhoton"]
        
        try:
            genpho = genpho[ak.argsort(genpho["pt"], ascending=False)]
        except:
            genpho = genpho

        genpho = col_defs.get_first_copy(genpho)

        mother = genpho.parent

        #check if there is a top in the b origin

        mother_is_lepton = ((abs(mother.pdgId)==11) | (abs(mother.pdgId)==13) | (abs(mother.pdgId)==15))
        mother_is_w_or_b = ((abs(mother.pdgId)==24) | (abs(mother.pdgId)==5))
        mother_is_w = (abs(mother.pdgId)==24)
        mother_is_b = (abs(mother.pdgId)==5)
        mother_is_top = ((abs(mother.pdgId)==6))
        t_channel_gluon = (abs(mother.pdgId)==21)

        #starts by being always true
        not_from_top = (genpho.pdgId==22)

        while not ak.all(ak.is_none(mother, axis=1)):
            not_from_top = (not_from_top & (ak.fill_none(abs(mother["pdgId"]), 0) != 6))
            mother = mother.parent

        #reset the mothers
        mother = genpho.parent

        #if the photon is emitted from the second copy of the top it counts as decay, according to Malgorzata
        #just for tests
        #genp=ak.firsts(genpho)
        #genp = genp[ak.any(mother_is_top,axis=-1)]
        #genp = genp[abs(genp.parent.parent.pdgId)==6]
        #genp = genp[~ak.is_none(genp)]

        is_top_decay = (mother_is_top & (ak.fill_none(mother.parent.pdgId,0)==mother.pdgId))
        
        is_from_decay = ((mother_is_lepton) | (~not_from_top & mother_is_w_or_b) | (is_top_decay))
        is_from_decay_lep = (mother_is_lepton)
        is_from_decay_wb = (~not_from_top & mother_is_w_or_b)
        is_from_decay_w = (~not_from_top & mother_is_w)
        is_from_decay_b = (~not_from_top & mother_is_b)
        is_from_decay_top = (is_top_decay)
        
        is_top_prod = (((mother_is_top) & (~is_top_decay)) | t_channel_gluon)
        is_ISR_prod = ((~mother_is_top) & (~is_from_decay) & (~t_channel_gluon))

        cats = {}
        
        #do only for the leading gen photon for simplicity and to remove ambiguity
        leadpho_from_production_top = ak.fill_none(ak.firsts(is_top_prod),False)
        leadpho_from_production_isr = ak.fill_none(ak.firsts(is_ISR_prod),False)
        leadpho_from_decay = ak.fill_none(ak.firsts(is_from_decay),False)
        leadpho_from_decay_lep = ak.fill_none(ak.firsts(is_from_decay_lep),False)
        leadpho_from_decay_wb = ak.fill_none(ak.firsts(is_from_decay_wb),False)
        leadpho_from_decay_w = ak.fill_none(ak.firsts(is_from_decay_w),False)
        leadpho_from_decay_b = ak.fill_none(ak.firsts(is_from_decay_b),False)
        leadpho_from_decay_top = ak.fill_none(ak.firsts(is_from_decay_top),False)

        cats["production"] = ((ak.num(genpho)>0) & (~leadpho_from_decay))
        #cats["productiontop"] = ak.fill_none((ak.num(genpho)>0) & leadpho_from_production_top,False)
        #cats["productionISR"] = ak.fill_none((ak.num(genpho)>0) & leadpho_from_production_isr,False)
        cats["decay"] = ((ak.num(genpho)>0) & leadpho_from_decay)
        #cats["decaylep"] = ak.fill_none((ak.num(genpho)>0) & leadpho_from_decay_lep,False)
        #cats["decaywb"] = ak.fill_none((ak.num(genpho)>0) & leadpho_from_decay_wb,False)
        #cats["decayw"] = ak.fill_none((ak.num(genpho)>0) & leadpho_from_decay_w,False)
        #cats["decayb"] = ak.fill_none((ak.num(genpho)>0) & leadpho_from_decay_b,False)
        #cats["decaytop"] = ak.fill_none((ak.num(genpho)>0) & leadpho_from_decay_top,False)
        cats["nophoton"] = (ak.num(genpho)==0)

        return cats
    
    def good_mass_genlepton_pair(self,data):
        """Which events have lepton pair mass required by the configuration"""
        return (data["genmll"] > 30)
    
    def good_mass_genlepton_pair_partlevel(self,data):
        """Which events have lepton pair mass required by the configuration"""
        return (data["genmllPartLevel"] > 30)

    def genmass_lepton_pair(self, data):
        """Return invariant mass of lepton pair."""
        genlepton = ak.pad_none(data["GenLepton"],2)
        return (genlepton[:, 0] + genlepton[:, 1]).mass

    def genmass_lepton_pair_partlevel(self, data):
        """Return invariant mass of lepton pair."""
        return (data["GenDressedLepton"][:, 0] + data["GenDressedLepton"][:, 1]).mass

    def photon_from_decay(self,data):

        genpho_is_decay = (data["decay"] | data["nophoton"])
        
        return genpho_is_decay
    
    def photon_from_production(self,data):

        genpho_is_production = data["production"]
        
        return genpho_is_production

    def genDeltaYTops(self, is_mc, data):

        genTop = data["GenTopPos"]
        genAntiTop = data["GenTopNeg"]
        genTop = ak.pad_none(genTop,1)
        genAntiTop = ak.pad_none(genAntiTop,1)
        yGenTop = abs(col_defs.rapidity(genTop[:,0]))
        yGenAntiTop = abs(col_defs.rapidity(genAntiTop[:,0]))
        deltaYtops = yGenTop - yGenAntiTop

        return deltaYtops

    def genDRphoClosLep(self, is_mc, data):

        genLep = data["GenLepton"]
        genLep =  ak.pad_none(genLep,1,axis=1)

        genPhoton = data["GenPhoton"]
        genPhoton = ak.pad_none(genPhoton,1,axis=1)

        gendeltar = ak.min(genPhoton[:, 0].metric_table(genLep),axis=-1)

        gendeltar = ak.firsts(gendeltar)

        return gendeltar

    def genDRphoClosTop(self, is_mc, data):

        genTop = data["GenTop"]
        genTop = genTop[ak.argsort(genTop.pdgId, ascending=False)]
        #ptGenTop = genTop.pt
        #genTop = genTop[ak.argsort(ptGenTop, ascending=False)]

        genPhoton = data["GenPhoton"]

        genTop = ak.pad_none(genTop,2,axis=1)
        genPhoton = ak.pad_none(genPhoton,1,axis=1)

        deltaphi0 = np.abs(genTop[:, 0].phi-genPhoton[:, 0].phi)
        deltaphi0 = ak.where(deltaphi0<np.pi,deltaphi0,2*np.pi-deltaphi0)

        deltaeta0 = genTop[:, 0].eta-genPhoton[:,0].eta

        deltaphi1 = np.abs(genTop[:, 1].phi-genPhoton[:, 0].phi)
        deltaphi1 = ak.where(deltaphi1<np.pi,deltaphi1,2*np.pi-deltaphi1)

        deltaeta1 = genTop[:, 1].eta-genPhoton[:,0].eta

        gendeltar0 = np.hypot(deltaeta0,deltaphi0)
        gendeltar1 = np.hypot(deltaeta1,deltaphi1)

        gendeltar = ak.where(gendeltar0<gendeltar1,gendeltar0,gendeltar1)

        return gendeltar

    def genDRphottbar(self, is_mc, data):

        genTop = data["GenTop"]
        genTop = ak.pad_none(genTop,2,axis=1)

        ttbar = genTop[:,0]+genTop[:,1]

        genPhoton = data["GenPhoton"]
        genPhoton = ak.pad_none(genPhoton,1,axis=1)

        deltaphi = np.abs(ttbar.phi-genPhoton[:, 0].phi)
        deltaphi = ak.where(deltaphi<np.pi,deltaphi,2*np.pi-deltaphi)

        deltaeta = ttbar.eta-genPhoton[:,0].eta

        gendeltar = np.hypot(deltaeta,deltaphi)

        return gendeltar
        
    def genmttbar(self, is_mc, data):

        genTop = data["GenTop"]
        genTop = ak.pad_none(genTop,2,axis=1)

        ttbar = genTop[:,0]+genTop[:,1]

        mttbar = ttbar.mass

        return mttbar

    def genmttgamma(self, is_mc, data):

        genTop = data["GenTop"]
        genTop = ak.pad_none(genTop,2,axis=1)

        ttbar = genTop[:,0]+genTop[:,1]
        
        genPhoton = data["GenPhoton"]
        genPhoton = ak.pad_none(genPhoton,1,axis=1)

        mttgamma = (ttbar+genPhoton[:,0]).mass

        return mttgamma

    def ngenphotons(self, data):
    
        npho = {}
        npho["zeropartlevelphotons"] = (ak.num(data["GenIsolatedPhoton"])==0)
        npho["exactly1partlevelphoton"] = (ak.num(data["GenIsolatedPhoton"])==1)
        npho["morethan1partlevelphoton"] = (ak.num(data["GenIsolatedPhoton"])>1)

        #genlep = data["GenLepton"]
        genpho = data["GenPhoton"]
        #has_lep_close = ak.any(genpho.metric_table(genlep) < 0.1, axis=2)
        #genpho = genpho[~has_lep_close]

        npho["zerophotons"] = (ak.num(genpho)==0)
        npho["exactly1photon"] = (ak.num(genpho)==1)
        npho["morethan1photon"] = (ak.num(genpho)>1)

        return npho


    def add_me_uncertainties(self, dsname, selector):
        """Matrix-element renormalization and factorization scale"""
        # Get describtion of individual columns of this branch with
        # Events->GetBranch("LHEScaleWeight")->GetTitle() in ROOT
        data = selector.data
        if dsname + "_LHEScaleSumw" in self.config["mc_lumifactors"]:
            norm = self.config["mc_lumifactors"][dsname + "_LHEScaleSumw"]
            if len(norm) == 44:
                # See https://github.com/cms-nanoAOD/cmssw/issues/537
                idx = [34, 5, 24, 15]
            elif len(norm) == 9:
                # This appears to be the standard case for most data sets
                idx = [7, 1, 5, 3]
            elif len(norm) == 8:
                # Same as length 9, just missing the nominal weight at index 4
                idx = [6, 1, 4, 3]
            elif len(norm) == 18:
                # Two sets of scale varations. From the titles in NanoAOD
                # the exact order is not clear. Assume the right one comes
                # first.
                idx = [14, 2, 10, 6]
            else:
                raise RuntimeError(
                    "Unexpected length of the norm for LHEScaleWeight: "
                    f"{len(norm)}")
            selector.set_systematic(
                "MEren",
                data["LHEScaleWeight"][:, idx[0]],#* abs(norm[idx[0]]),
                data["LHEScaleWeight"][:, idx[1]])#* abs(norm[idx[1]]))
            selector.set_systematic(
                "MEfac",
                data["LHEScaleWeight"][:, idx[2]],#* abs(norm[idx[2]]),
                data["LHEScaleWeight"][:, idx[3]])#* abs(norm[idx[3]]))

    def add_ps_uncertainties(self, dsname, selector):
        """Parton shower scale uncertainties"""
        data = selector.data
        psweight = data["PSWeight"]
        if len(psweight) == 0:
            return
        num_weights = ak.num(psweight)[0]
        if num_weights == 1:
            # NanoAOD containts one 1.0 per event in PSWeight if there are no
            # PS weights available, otherwise all counts > 1.
            return
        if num_weights == 4:
            if self.config["year"].startswith("ul"):
                # Workaround for PSWeight number changed their order in
                # NanoAODv8, meaning non-UL is unaffected
                selector.set_systematic(
                    "PSisr", psweight[:, 0], psweight[:, 2])
                selector.set_systematic(
                    "PSfsr", psweight[:, 1], psweight[:, 3])
            else:
                selector.set_systematic(
                    "PSisr", psweight[:, 2], psweight[:, 0])
                selector.set_systematic(
                    "PSfsr", psweight[:, 3], psweight[:, 1])
        else:
            raise RuntimeError(
                "Unexpected length of the PSWeight: "
                f"{num_weights}")

    def add_pdf_uncertainties(self, dsname, selector):
        """Add PDF uncertainties, using the methods described here:
        https://arxiv.org/pdf/1510.03865.pdf#section.6"""
        data = selector.data
        if ("LHEPdfWeight" not in data.fields
                or "pdf_types" not in self.config):
            return

        split_pdf_uncs = False
        if "split_pdf_uncs" in self.config:
            split_pdf_uncs = self.config["split_pdf_uncs"]
        pdfs = data["LHEPdfWeight"]

        normalize_pdf_uncs = False
        if "normalize_pdf_uncs" in self.config:
            normalize_pdf_uncs = self.config["normalize_pdf_uncs"]

        pdf_doc = pdfs.__doc__
        pdf_type = None
        for LHA_ID, _type in self.config["pdf_types"].items():
            if LHA_ID in pdf_doc:
                pdf_type = _type.lower()

        if normalize_pdf_uncs:
            if dsname + "_LHEPdfSumw" not in self.config["mc_lumifactors"]:
                raise pepper.config.ConfigError(
                    "Missing lumifactors for PDF uncertainties for dataset "
                    f"'{dsname}'. Please run compute_mc_lumifactors.py with "
                    "the '-p' option.")
            norm = self.config["mc_lumifactors"][dsname + "_LHEPdfSumw"]
            pdfs = pdfs * abs(np.array(norm)[np.newaxis, :])

        # Check if sample has alpha_s variations - currently assuming number of
        # regular variations is a multiple of 10
        if len(data) == 0:
            has_as_unc = False
        else:
            has_as_unc = (len(pdfs[0]) % 10) > 1
            # Workaround for "order of scale and pdf weights not consistent"
            # See https://twiki.cern.ch/twiki/bin/view/CMS/MCKnownIssues
            if ak.mean(pdfs[0]) < 0.6:  # approximate, see if factor 2 needed
                pdfs = ak.without_parameters(pdfs)
                pdfs = ak.concatenate([pdfs[:, 0:1], pdfs[:, 1:] * 2], axis=1)
        n_offset = -2 if has_as_unc else None

        if split_pdf_uncs:
            # Just output variations - user
            # will need to combine these for limit setting
            num_variation = len(pdfs[0]) + (n_offset or 0)
            if pdf_type == "true_hessian" or pdf_type == "hessian":
                # First element is central value - adjust all other
                # elements relative to this
                selector.set_systematic(
                    "PDF", *[pdfs[:, i] - pdfs[:, 0] + 1
                             for i in range(1, num_variation)],
                    scheme="numeric")
                if has_as_unc:
                    selector.set_systematic(
                        "PDFalphas",
                        pdfs[:, -1] - pdfs[:, 0] + 1,
                        pdfs[:, -2] - pdfs[:, 0] + 1)
            elif pdf_type.startswith("mc"):
                selector.set_systematic(
                    "PDF",
                    *[pdfs[:, i] for i in range(num_variation)],
                    scheme="numeric")
                if has_as_unc:
                    selector.set_systematic(
                        "PDFalphas", pdfs[:, -1], pdfs[:, -2])
            elif pdf_type is None:
                raise pepper.config.ConfigError(
                    "PDF LHA Id not included in config. PDF docstring is: "
                    + pdf_doc)
            else:
                raise pepper.config.ConfigError(
                    f"PDF type {pdf_type} not recognised. Valid options "
                    "are 'True_Hessian', 'Hessian', 'MC' and 'MC_Gaussian'")
        else:
            if pdf_type == "true_hessian":
                # Treatment of true hessian uncertainties, for e.g. CTEQ
                # or HERA sets
                eigen_vals = ak.to_numpy(pdfs[:, 1:n_offset])
                eigen_vals = eigen_vals.reshape(
                    (eigen_vals.shape[0], eigen_vals.shape[1] // 2, 2))
                central, eigenvals = ak.broadcast_arrays(
                    pdfs[:, 0, None, None], eigen_vals)
                var_up = ak.max((eigen_vals - central), axis=2)
                var_up = ak.where(var_up > 0, var_up, 0)
                var_up = np.sqrt(ak.sum(var_up ** 2, axis=1))
                var_down = ak.max((central - eigen_vals), axis=2)
                var_down = ak.where(var_down > 0, var_down, 0)
                var_down = np.sqrt(ak.sum(var_down ** 2, axis=1))
                unc = None
            if pdf_type == "hessian":
                # Treatment of pseudo hessian uncertainties, for e.g. NNPDF
                # or pdf4LHC sets
                eigen_vals = ak.to_numpy(pdfs[:, 1:n_offset])
                variations = eigen_vals - pdfs[:, 0, None]
                unc = np.sqrt(ak.sum(variations ** 2, axis=1))
            elif pdf_type == "mc":
                # ak.sort produces an error here. Work-around:
                variations = np.sort(ak.to_numpy(pdfs[:, 1:n_offset]))
                nvar = ak.num(variations)[0]
                unc = (variations[:, int(round(0.841344746*nvar))]
                       - variations[:, int(round(0.158655254*nvar))]) / 2
            elif pdf_type == "mc_gaussian":
                mean = ak.mean(pdfs[:, 1:n_offset], axis=1)
                unc = np.sqrt((ak.sum(pdfs[:, 1:n_offset] - mean) ** 2)
                              / (ak.num(pdfs)[0] - (3 if n_offset else 1)))
            elif pdf_type is None:
                raise pepper.config.ConfigError(
                    "PDF LHA Id not included in config. PDF docstring is: "
                    + pdf_doc)
            else:
                raise pepper.config.ConfigError(
                    f"PDF type {pdf_type} not recognised. Valid options "
                    "are 'True_Hessian', 'Hessian', 'MC' and 'MC_Gaussian'")

            # Add PDF alpha_s uncertainties
            if has_as_unc:
                if ("combine_alpha_s" in self.config and
                        self.config["combine_alpha_s"]):
                    alpha_s_unc = (pdfs[:, -1] - pdfs[:, -2]) / 2
                    if unc is not None:
                        unc = np.sqrt(unc ** 2 + alpha_s_unc ** 2)
                    else:
                        var_up = np.sqrt(var_up ** 2 + alpha_s_unc ** 2)
                        var_down = np.sqrt(var_down ** 2 + alpha_s_unc ** 2)
                else:
                    selector.set_systematic(
                        "PDFalphas", pdfs[:, -1], pdfs[:, -2])
            if unc is not None:
                selector.set_systematic("PDF", 1 + unc, 1 - unc)
            else:
                selector.set_systematic("PDF", 1 + var_up, 1 - var_down)



