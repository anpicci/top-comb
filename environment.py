# settings.py
import os
from datetime import datetime
from dataclasses import dataclass

cwd = os.getcwd()

@dataclass
class TopCombEnv:
    # CHANGE THIS for your environment or override in CI/CD
    mainpath: str = cwd
    outpath: str = "/eos/user/c/cvicovil/www/top-comb/"

    # Other paths
    workdir: str = f"{mainpath}/workdirs/" 

    # Configurations related to Generation 
    genproductions: str = f"{mainpath}/genproductions_scripts"
    genproductions_repo: str = "https://gitlab.cern.ch/cvicovil/genproductions_scripts.git"
    genproductions_image: str = "/cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el7:x86_64"
    genproductions_branch: str = "topcomb_eft_mg265"

    # TMG tools configurations
    tmgtools: str = f"{mainpath}/tmg-tools/top-gendqm"
    tmgtools_campaign: str = "RunIISummer20UL18"

    # Configurations related to Reinterpretation
    cmgrdf: str = f"{mainpath}/cmgrdf-prototype"

    # Configurations related to combine
    combine_path: str = f"{mainpath}/combine/"
    combine_image: str = "/cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el7:x86_64"
    combine_scram: str = "slc7_amd64_gcc900"
    combine_cmsrel: str = "CMSSW_11_3_4"
    combine_comb_branch: str ="ajgilbert/deep-minimize"
    combine_ch_branch: str ="kezhuguo/parallel-hessian"

    # Gridpack info
    @classmethod
    def new( cls, **args ):
        return cls(
            **args
        )


    def model_dump(self):
        return self.__dict__ 

