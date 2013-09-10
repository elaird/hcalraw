#!/usr/bin/env python


def opts():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("--file1", dest="file1", default="", help="REQUIRED: .root file over which to run")
    parser.add_option("--feds1", dest="feds1", default="", help="REQUIRED: FEDs to use in file1")
    parser.add_option("--file2", dest="file2", default="", help=".root file to compare with file1")
    parser.add_option("--feds2", dest="feds2", default="", help="FEDs to use in file2")
    parser.add_option("--patterns", dest="patterns", default=False, action="store_true", help="interpret QIE data as FE patterns")
    parser.add_option("--nevents", dest="nevents", default="", metavar="N", help="stop after N events")

    options, args = parser.parse_args()

    if not all([options.file1, options.feds1]):
        parser.print_help()
        exit()
    return options


options = opts()
if not all([x[0] == "_" or x in ["x", "opts", "options"] for x in dir()]):
    print dir()
    print "Please put imports after this block, to prevent PyROOT from stealing '--help'."


if options.nevents:
    try:
        nEvents = int(options.nevents)
    except ValueError:
        print "ERROR: nevents '%s' cannot be converted to an int." % options.nevents
        exit()
else:
    nEvents = None


import analyze

label = "latest"
analyze.oneRun(file1=options.file1,
               feds1=options.feds1,
               file2=options.file2,
               feds2=options.feds2,
               nEvents=nEvents,
               patternMode=options.patterns,
               label=label,
               )

if not options.patterns:
    if options.file2:
        analyze.printHisto(label)
    import graphs
    graphs.makeSummaryPdf(labels=[label])
