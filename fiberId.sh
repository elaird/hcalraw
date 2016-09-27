#!/bin/bash

RUN=$1
COMMON=root://eoscms.cern.ch//store/group/dpg_hcal/comm_hcal
if [[ ( "$RUN" < 264261 ) ]] ; then
    FILE=$COMMON/archival/20160914_USC_LS1_runs212958-264260/USC_${RUN}.root
else
    FILE=$COMMON/USC/USC_${RUN}.root
fi

echo "VME (run $RUN)"
./oneRun.py --file1=${FILE} --feds1=HCAL  --patterns | ./diff.py data/ref_vme_G.txt
echo
echo "uTCA (run $RUN)"
./oneRun.py --file1=${FILE} --feds1=uHBECF --patterns | ./diff.py data/ref_utca_G.txt
