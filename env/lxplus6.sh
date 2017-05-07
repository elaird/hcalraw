source /cvmfs/cms.cern.ch/cmsset_default.sh

export SCRAM_ARCH=slc6_amd64_gcc630
cd /cvmfs/cms.cern.ch/${SCRAM_ARCH}/cms/cmssw/CMSSW_9_0_1/src
eval `scramv1 runtime -sh`
cd - > /dev/null

# source /afs/cern.ch/project/eos/installation/cms/etc/setup.sh
