#!/bin/bash

RUN=$1
FILE=root://eoscms.cern.ch//store/group/dpg_hcal/comm_hcal/LS1/USC_${RUN}.root

echo "VME (run $RUN)"
./oneRun.py --file1=${FILE} --feds1=HCAL  --patterns | ./diff.py data/ref_vme_G.txt
echo
echo "uTCA (run $RUN)"
./oneRun.py --file1=${FILE} --feds1=uHBECF --patterns | ./diff.py data/ref_utca_G.txt
