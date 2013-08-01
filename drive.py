#!/usr/bin/env python

from analyze import oneRun, printHisto

baseDir = "/afs/cern.ch/user/e/elaird/work/public/d1_utca/"

#oneRun(utcaFileName=baseDir+"/usc/USC_209150.root",
#       cmsFileName=baseDir+"/castor/209151.HLTSkim.root",
#       label="Run209151",
#       useEvn=False,
#       filterEvn=False,
#       )

# 211155
#label = "Run211155"
#oneRun(utcaFileName=baseDir+"/usc/USC_211155.root",
#       cmsFileName=baseDir+"/usc/USC_211154.root",
#       cmsIsLocal=True,
#       label=label,
#       useEvn=False,
#       filterEvn=False,
#       )

#oneRun(utcaFileName=baseDir+"/usc/USC_211428.root",
#       cmsFileName=baseDir+"/usc/USC_211427.root",
#       cmsIsLocal=True,
#       label="Run211428",
#       useEvn=False,
#       filterEvn=False,
#       )

run = 42
label = "Run%d" % run
fileName = baseDir+"/904/B904_Integration_%06d.root" % run
oneRun(utcaFileName=fileName,
       utcaFedIds=[931],
       cmsFileName=fileName,
       cmsFedIds=[702],
       cmsIsLocal=True,
       label=label,
       useEvn=False,
       filterEvn=False,
       ornTolerance=1,
       uhtr=True,
       printEventMap=False,
       )

#run = 212928
#label = "Run%d" % run
#oneRun(#utcaFileName=fileName,
#       #utcaFedIds=[931],
#       cmsFileName="~elaird/USC_%d.root" % run,
#       cmsFedIds=[725],#range(724, 732),
#       cmsIsLocal=True,
#       label=label,
#       useEvn=False,
#       filterEvn=False,
#       ornTolerance=1,
#       uhtr=True,
#       printEventMap=False,
#       )

printHisto(label)
#import graphs
#graphs.makeSummaryPdf(labels=[label])
