# settings.py
import os
from datetime import datetime
from dataclasses import dataclass, field

cwd = os.getcwd()

@dataclass
class TopCombEnv:
    # CHANGE THIS for your environment or override in CI/CD
    mainpath: str = cwd
    eos_redirector: str = "root://eosuser.cern.ch/"
    outpath: str = "/eos/cms/store/group/phys_top/cvicovil/top-comb/"

    # Other paths
    workdir: str = f"{mainpath}/workdirs/" 
    measurements_path: str = f"{mainpath}/measurements/"

    # Configurations related to Generation 
    genproductions: str = f"{mainpath}/genproductions_scripts"
    genproductions_repo: str = "https://gitlab.cern.ch/cvicovil/genproductions_scripts.git"
    genproductions_image: str = "/cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el7:x86_64"
    genproductions_branch: str = "topcomb_eft_mg265"

    # MC production tools configurations
    mcprod: str = f"{mainpath}/mc-prod"

    # Configurations related to Reinterpretation
    cmgrdf: str = f"{mainpath}/cmgrdf-prototype"
    lumis: dict = field(default_factory=lambda: {
        "Run2" : 16.81 + 19.50 +  41.48 + 59.83
        }
    )

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

