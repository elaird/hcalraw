#!/usr/bin/env python

import optparse
import analyze
import graphs


def opts():
    parser = optparse.OptionParser()
    parser.add_option("--run", dest="run", default=None,
                      metavar="N",
                      help="run number")
    parser.add_option("--dir", dest="dir", default="/afs/cern.ch/user/e/elaird/work/public/d1_utca/",
                      help="directory in which ROOT files sit")
    parser.add_option("--file", dest="file", default="",
                      help=".root file over which to run")
    parser.add_option("--patterns", dest="patterns", default=False, action="store_true", help="interpret QIE data as FE patterns")

    options, args = parser.parse_args()
    try:
        options.file or int(options.run)
    except TypeError:
        parser.print_help()
        exit()
    return options

options = opts()
if options.file:
    run = None
    label = "latest"
else:
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


if run <= 200000:  # including None
    if options.file:
        fileName = options.file
    else:
        fileName = baseDir+"/904/B904_Integration_%06d.root" % run
    analyze.oneRun(utcaFileName=fileName if not options.patterns else "",
                   utcaFedIds=[931],
                   cmsFileName=fileName,
                   cmsFedIds=[702],
                   cmsIsLocal=True,
                   cmsPatternMode=options.patterns,
                   label=label,
                   useEvn=False,
                   filterEvn=False,
                   ornTolerance=1,
                   uhtr=True,
                   printEventMap=False,
                   )

if not options.patterns:
    analyze.printHisto(label)
    graphs.makeSummaryPdf(labels=[label])
