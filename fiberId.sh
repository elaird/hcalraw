#!/bin/bash

RUN=$1
COMMON=root://eoscms.cern.ch//store/group/dpg_hcal/comm_hcal
if [[ ( "$RUN" < 264261 ) ]] ; then
    FILE=$COMMON/archival/20160914_USC_LS1_runs212958-264260/USC_${RUN}.root
elif [[ ( "$RUN" < 280486 ) ]] ; then
    FILE=$COMMON/USC/USC_${RUN}.root
elif [[ ( "$RUN" < 99999999 ) ]] ; then
    FILE=$COMMON/USC/run${RUN}/USC_${RUN}.root
else
    FILE=$1
fi

./oneRun.py --file1=${FILE} --feds1=HCAL --plugins=patterns ${@:2} | ./diff.py data/ref_2017_v1.txt
