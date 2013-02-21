#http://root.cern.ch/phpBB3/viewtopic.php?f=3&t=9951&p=42716&hilit=pyroot+lxplus#p42716
#http://root.cern.ch/phpBB3/viewtopic.php?f=3&t=11374&p=49129&hilit=GLIBCXX_3.4.9#p49129

TAG=x86_64-slc5-gcc43-opt
ROOT="5.32.01/${TAG}"
GCC="4.3.2"
PYTHON="2.6.5"
BASEDIR=/afs/cern.ch/sw/lcg/


if [[ "$BASEDIR" ]]; then
source ${BASEDIR}/contrib/gcc/${GCC}/${TAG}/setup.sh ${BASEDIR}/contrib
    source ${BASEDIR}/app/releases/ROOT/${ROOT}/root/bin/thisroot.sh

    export PATH=${BASEDIR}/contrib/gcc/${GCC}/${TAG}/bin:${PATH}
    export LD_LIBRARY_PATH=${BASEDIR}/contrib/gcc/${GCC}/${TAG}/lib64:${LD_LIBRARY_PATH}

    export PATH=${BASEDIR}/external/Python/${PYTHON}/${TAG}/bin:${PATH}
    export LD_LIBRARY_PATH=${BASEDIR}/external/Python/${PYTHON}/${TAG}/lib:${LD_LIBRARY_PATH}
fi