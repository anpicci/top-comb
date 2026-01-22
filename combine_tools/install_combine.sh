#!/usr/bin/env bash
# Install Combine & CombineHarvester in a configurable way.
# Example: ./install_combine.sh -p ${PWD} -a slc7_amd64_gcc900 -r CMSSW_11_3_4  

source /cvmfs/cms.cern.ch/cmsset_default.sh

# Defaults
SCRAM_ARCH_DEFAULT="slc7_amd64_gcc900"
CMSREL_DEFAULT="CMSSW_11_3_4"
EFTCOMBPATH_DEFAULT=`pwd`
COMB_BRANCH_DEFAULT="deep-minimize"
CH_BRANCH_DEFAULT="kezhuguo/parallel-hessian"

print_usage() {
  cat <<EOF
Usage: $0 -p EFTCOMBPATH [-a SCRAM_ARCH] [-r CMSREL] [-b COMB_BRANCH] [-c CH_BRANCH] [-j JOBS] [-w WORKDIR]
  -p EFTCOMBPATH   Path to your eft-combination-cms repository (required)
  -a SCRAM_ARCH    SCRAM_ARCH to use (default: ${SCRAM_ARCH_DEFAULT})
  -r CMSREL        CMS release to setup (default: ${CMSREL_DEFAULT})
  -b COMB_BRANCH   Combine branch or remote/ref to checkout (default: ${COMB_BRANCH_DEFAULT})
  -c CH_BRANCH     CombineHarvester branch or remote/ref (default: ${CH_BRANCH_DEFAULT})
  -h               Show this help
EOF
}

# Parse args
SCRAM_ARCH="${SCRAM_ARCH_DEFAULT}"
CMSREL="${CMSREL_DEFAULT}"
EFTCOMBPATH="${EFTCOMBPATH_DEFAULT}"
COMB_BRANCH="${COMB_BRANCH_DEFAULT}"
CH_BRANCH="${CH_BRANCH_DEFAULT}"
JOBS="${JOBS_DEFAULT}"
WORKDIR="${WORKDIR_DEFAULT}"

while getopts "a:r:p:b:c:j:w:h" opt; do
  case "${opt}" in
    a) SCRAM_ARCH="${OPTARG}" ;;
    r) CMSREL="${OPTARG}" ;;
    p) EFTCOMBPATH="${OPTARG}" ;;
    b) COMB_BRANCH="${OPTARG}" ;;
    c) CH_BRANCH="${OPTARG}" ;;
    h) print_usage; exit 1 ;;
    *) print_usage; exit 1 ;;
  esac
done


# Resolve absolute paths
EFTCOMBPATH="$(realpath "${EFTCOMBPATH}")"
export SCRAM_ARCH="${SCRAM_ARCH}"


setup_folder() {
  if [[ -d "${EFTCOMBPATH}/combine" ]]; then
    echo "A combine release already exists in $EFTCOMBPATH. Remove or change this parameter to reinstall a new one."
    exit 0
  else
    mkdir "${EFTCOMBPATH}/combine"
  fi
  cd "${EFTCOMBPATH}/combine"
}

setup_cmssw() {
  if [[ -d "${CMSREL}" ]]; then
    echo "Using existing CMSSW area: ${CMSREL}"
  else
    echo "Creating CMSSW release ${CMSREL} ..."
    cmsrel "${CMSREL}"
  fi
  cd "${CMSREL}/src"
  cmsenv
}

install_combine() {
    repo_dir="HiggsAnalysis/CombinedLimit"
    if [[ -d "${repo_dir}" ]]; then
      echo "Combine repository already exists at ${repo_dir}, fetching/updating..."
    else
      echo "Cloning Combine..."
      git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git "${repo_dir}"
    fi
    cd "${repo_dir}"

    COMB_PATH=$( realpath "${repo_dir}" )

    local remote_name="${COMB_BRANCH%%/*}"
    local branch_name="${COMB_BRANCH#*/}"
    git remote add "${remote_name}" "https://github.com/${remote_name}/HiggsAnalysis-CombinedLimit.git"
    git fetch "${remote_name}" "${remote_branch}"
    git checkout -b "${remote_branch}" "${remote_branch}/${remote_branch}"

    # Ensure python physics models are linked
    cd python 
    ln -s "${EFTCOMBPATH}"/combine_tools/EFTHybrid.py ./
    ln -s "${EFTCOMBPATH}"/combine_tools/EFTComposite.py ./
    cd ${COMB_PATH}

    echo "Building Combine..."
    scram b -j 4 
}

install_combineharvester() {

    repo_dir="CombineHarvester"
    if [[ -d "${repo_dir}" ]]; then
      echo "CombineHarvester repository already exists at ${repo_dir}, fetching/updating..."
    else
      echo "Cloning CombineHarvester..."
      git clone https://github.com/cms-analysis/CombineHarvester.git "${repo_dir}"
    fi
    scramv1 b clean; scramv1 b

    pushd "${repo_dir}"
    local remote_name="${CH_BRANCH%%/*}"
    local branch_name="${CH_BRANCH#*/}"
 
    git remote add ${remote_name} https://github.com/kezhuguo/CombineHarvester.git
    git fetch ${remote_name} ${remote_branch}
    git checkout -b ${branch_name} ${remote_name}/${branch_name}
    popd
    scram b -j 4 

}

main() {
  echo "Configuration:"
  echo "  SCRAM_ARCH = ${SCRAM_ARCH}"
  echo "  CMSREL     = ${CMSREL}"
  echo "  EFTCOMBPATH= ${EFTCOMBPATH}"
  echo "  COMB_BRANCH= ${COMB_BRANCH}"
  echo "  CH_BRANCH  = ${CH_BRANCH}"

  setup_folder  
  setup_cmssw
  #install_combine
  #install_combineharvester

  cd ${EFTCOMBPATH}

  echo "Done."
}

main "$@"
