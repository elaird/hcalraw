source /cvmfs/cms.cern.ch/cmsset_default.sh

export SCRAM_ARCH=slc6_amd64_gcc493
cd /cvmfs/cms.cern.ch/${SCRAM_ARCH}/cms/cmssw/CMSSW_8_0_3/src
eval `scramv1 runtime -sh`
cd - > /dev/null

source /afs/cern.ch/project/eos/installation/cms/etc/setup.sh
export LS1=root://eoscms.cern.ch//store/group/dpg_hcal/comm_hcal/LS1
export USC=root://eoscms.cern.ch//store/group/dpg_hcal/comm_hcal/USC
