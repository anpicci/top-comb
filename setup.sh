mode=$1
case $mode in
    reinterpret)
        #!/bin/bash
        source /cvmfs/sft.cern.ch/lcg/views/LCG_106a_cuda/x86_64-el9-gcc11-opt/setup.sh
        pushd cmgrdf-prototype
        eval $(make env)
        popd
        ;;
    *)
        echo "Unknown mode: $mode"
        exit 1
        ;;
esac
