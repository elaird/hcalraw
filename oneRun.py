#!/usr/bin/env python


def opts():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("--file1", dest="file1", default="", help="REQUIRED: .root file over which to run")
    parser.add_option("--feds1", dest="feds1", default="", help="REQUIRED: FEDs to use in file1, e.g. 714,722")
    parser.add_option("--file2", dest="file2", default="", help=".root file to compare with file1")
    parser.add_option("--feds2", dest="feds2", default="", help="FEDs to use in file2, e.g. 931")
    parser.add_option("--patterns", dest="patterns", default=False, action="store_true", help="interpret QIE data as FE patterns")
    parser.add_option("--nevents", dest="nevents", default="", metavar="N", help="stop after N events")

    options, args = parser.parse_args()

    if not all([options.file1, options.feds1]):
        parser.print_help()
        exit()
    return options


def nEvents(s=""):
    if s:
        try:
            return int(s)
        except ValueError:
            print "ERROR: nevents '%s' cannot be converted to an int." % s
            exit()
    else:
        return None


def checkFeds(feds=[]):
    import configuration
    if len(set([configuration.isVme(fed) for fed in feds])) != 1:
        print "ERROR: fed list %s is mixed among uTCA and VME." % str(l)
        exit()


def fedList(s=""):
    if not s:
        return []
    out = [int(x) for x in s.split(",")]
    checkFeds(out)
    return out


def checkModules():
    import types
    names = []
    for key, value in globals().iteritems():
        if isinstance(value, types.ModuleType):
            names.append(key)
    if names != ["__builtins__"]:
        print names
        print "Please put imports after this block, to prevent PyROOT from stealing '--help'."


options = opts()
checkModules()

import analyze

label = "latest"
analyze.oneRun(file1=options.file1,
               feds1=fedList(options.feds1),
               file2=options.file2,
               feds2=fedList(options.feds2),
               nEvents=nEvents(options.nevents),
               patternMode=options.patterns,
               label=label,
               )

if not options.patterns:
    if options.file2:
        analyze.printHisto(label)
    import graphs
    graphs.makeSummaryPdf(labels=[label])
