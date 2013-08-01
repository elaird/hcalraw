#!/usr/bin/env python

import optparse
import analyze
import graphs


def opts():
    parser = optparse.OptionParser()
    parser.add_option("--run", dest="run", default=None,
                      metavar="N",
                      help="specify one run number")
    parser.add_option("--dir", dest="dir", default="/afs/cern.ch/user/e/elaird/work/public/d1_utca/",
                      help="specify directory in which ROOT files sit")

    options, args = parser.parse_args()
    return options

options = opts()
run = int(options.run)
label = "Run%d" % run
baseDir = options.dir

if run == 209151:
    analyze.oneRun(utcaFileName=baseDir+"/usc/USC_209150.root",
                   cmsFileName=baseDir+"/castor/209151.HLTSkim.root",
                   label=label,
                   useEvn=False,
                   filterEvn=False,
                   )

if run == 211155:
    analyze.oneRun(utcaFileName=baseDir+"/usc/USC_211155.root",
                   cmsFileName=baseDir+"/usc/USC_211154.root",
                   cmsIsLocal=True,
                   label=label,
                   useEvn=False,
                   filterEvn=False,
                   )

if run == 211428:
    analyze.oneRun(utcaFileName=baseDir+"/usc/USC_211428.root",
                   cmsFileName=baseDir+"/usc/USC_211427.root",
                   cmsIsLocal=True,
                   label=label,
                   useEvn=False,
                   filterEvn=False,
                   )


if run == 212928:
    analyze.oneRun(cmsFileName=baseDir+"/USC_%d.root" % run,
                   cmsFedIds=[725],#range(724, 732),
                   cmsIsLocal=True,
                   label=label,
                   useEvn=False,
                   filterEvn=False,
                   ornTolerance=1,
                   uhtr=True,
                   printEventMap=False,
                   )


if run <= 200000:
    fileName = baseDir+"/904/B904_Integration_%06d.root" % run
    analyze.oneRun(utcaFileName=fileName,
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

analyze.printHisto(label)
graphs.makeSummaryPdf(labels=[label])
