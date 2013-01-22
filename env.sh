#note that CASTOR will work only with some CMSSW versions
#see https://cern.service-now.com/service-portal/article.do?n=KB0001585

cd /afs/cern.ch/cms/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_7/src
eval `scramv1 runtime -sh`
cd - > /dev/null