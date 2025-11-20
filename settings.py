# settings.py
import os
from datetime import datetime

class TopCombSettings:
    def __init__( self ):
        # CHANGE THIS for your environment or override in CI/CD
        self.topcomb_outpath = "/eos/user/c/cvicovil/www/top-comb/"

        # Other paths
        self.topcomb_mainpath = os.getcwd()
        self.topcomb_workdir = f"{self.topcomb_mainpath}/workdirs/" 
        self.topcomb_genproductions = f"{self.topcomb_mainpath}/genproductions_scripts"
        self.topcomb_tmgtools = f"{self.topcomb_mainpath}/tmg-tools/top-gendqm"
        self.topcomb_cmgrdf = f"{self.topcomb_mainpath}/cmgrdf-prototype"

        # Gridpack info
        self.singularity_image_gridpack = "/cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el7:x86_64"
        self.genproductions_gridpack = "https://gitlab.cern.ch/cvicovil/genproductions_scripts.git"
        self.branch_gridpack = "topcomb_eft_mg265"

    def model_dump(self):
        return self.__dict__ 


# Usage
if __name__ == "__main__":
    settings = TopCombSettings()
    print(settings.model_dump())
