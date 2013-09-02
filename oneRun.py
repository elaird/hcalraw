#!/usr/bin/env python


def opts():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("--run", dest="run", default=None,
                      metavar="N",
                      help="run number")
    parser.add_option("--dir", dest="dir", default="/afs/cern.ch/user/e/elaird/work/public/d1_utca/",
                      help="(can be used with --run)")
    parser.add_option("--file", dest="file", default="",
                      help=".root file over which to run")
    parser.add_option("--patterns", dest="patterns", default=False, action="store_true", help="interpret QIE data as FE patterns")
    parser.add_option("--nevents", dest="nevents", default="", metavar="N", help="stop after N events")

    options, args = parser.parse_args()

    if not (options.file or options.run):
        parser.print_help()
        exit()
    try:
        options.file or int(options.run)
    except ValueError:
        print "ERROR: run number '%s' cannot be converted to an int." % options.run
        exit()

    return options


options = opts()
if not all([x[0] == "_" or x in ["x", "opts", "options"] for x in dir()]):
    print dir()
    print "Please put imports after this block, to prevent PyROOT from stealing '--help'."

if options.file:
    run = None
    label = "latest"
else:
    run = int(options.run)
    label = "Run%d" % run
    baseDir = options.dir

if options.nevents:
    try:
        nEvents = int(options.nevents)
    except ValueError:
        print "ERROR: nevents '%s' cannot be converted to an int." % options.nevents
        exit()
else:
    nEvents = None


import analyze
if run == 209151:
    analyze.oneRun(utcaFileName=baseDir+"/usc/USC_209150.root",
                   cmsFileName=baseDir+"/castor/209151.HLTSkim.root",
                   label=label,
                   useEvn=False,
                   filterEvn=False,
                   nEvents=nEvents,
                   )

if run == 211155:
    analyze.oneRun(utcaFileName=baseDir+"/usc/USC_211155.root",
                   cmsFileName=baseDir+"/usc/USC_211154.root",
                   cmsIsLocal=True,
                   label=label,
                   useEvn=False,
                   filterEvn=False,
                   nEvents=nEvents,
                   )

if run == 211428:
    analyze.oneRun(utcaFileName=baseDir+"/usc/USC_211428.root",
                   cmsFileName=baseDir+"/usc/USC_211427.root",
                   cmsIsLocal=True,
                   label=label,
                   useEvn=False,
                   filterEvn=False,
                   nEvents=nEvents,
                   )


if run >= 212928:
    analyze.oneRun(cmsFileName=baseDir+"/USC_%d.root" % run,
                   cmsFedIds=[725],#range(724, 732),
                   cmsIsLocal=True,
                   label=label,
                   useEvn=False,
                   filterEvn=False,
                   ornTolerance=1,
                   uhtr=True,
                   printEventMap=False,
                   nEvents=nEvents,
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
                   nEvents=nEvents,
                   )

if not options.patterns:
    import graphs
    analyze.printHisto(label)
    graphs.makeSummaryPdf(labels=[label])
