export SCRAM_ARCH=slc6_amd64_gcc481
cd /afs/cern.ch/cms/${SCRAM_ARCH}/cms/cmssw/CMSSW_7_3_5/src
eval `/afs/cern.ch/cms/common/scramv1 runtime -sh`
cd - > /dev/null

source /afs/cern.ch/project/eos/installation/cms/etc/setup.sh
export LS1=root://eoscms.cern.ch//store/group/dpg_hcal/comm_hcal/LS1
export USC=root://eoscms.cern.ch//store/group/dpg_hcal/comm_hcal/USC
