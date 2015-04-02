#!/usr/bin/env python

import analyze
import printer
import graphs
import sys
from configuration import sw, matching
from options import opts


def subset(options, l, process=False):
    out = {}
    for item in l:
        out[item] = getattr(options, item)
        if process:
            out[item] = sw.fedList(out[item])
    return out


def check(options):
    if not all([options.file1, options.feds1]):
        sys.exit("--file1 and --feds1 are required (see './oneRun.py --help').")
    if not options.outputFile.endswith(".root"):
        sys.exit("--output-file must end with .root (%s)" % options.outputFile)
    if options.feds2 and not options.file2:
        print "INFO: using --file1 also for --file2; also using identity map"
        options.file2 = options.file1
        options.identityMap = True


def go(options):
    kargs = subset(options, ["feds1", "feds2"], process=True)
    kargs.update(subset(options, ["file1", "file2", "nEvents", "nEventsSkip", "outputFile", "noUnpack", "patterns"]))

    kargs["compareOptions"] = subset(options, ["adcPlots", "anyEmap", "printEmap"])
    kargs["mapOptions"] = subset(options, ["printEventMap", "identityMap"])
    kargs["printOptions"] = subset(options, ["dump", "progress"])
    kargs["printOptions"]["warn"] = not options.noWarnUnpack
    kargs["printOptions"]["crateslots"] = sw.fedList(options.crateslots)

    analyze.oneRun(**kargs)


def main(options):
    check(options)

    if options.match:
        matching.tsRange = getattr(matching, "tsRange_%s" % options.match)
        matching.tsRange()  # call once to set utcaBcnDelta

    if options.noColor:
        printer.__color = False

    if options.patterns:
        options.nEvents = 1

    if not options.noLoop:
        analyze.setup()
        if options.profile:
            import cProfile
            cProfile.runctx("go(options)", globals(), locals(), sort="time")
        else:
            go(options)

    graphs.makeSummaryPdf(inputFiles=[options.outputFile],
                          feds1=sw.fedList(options.feds1),
                          feds2=sw.fedList(options.feds2),
                          pdf=options.outputFile.replace(".root", ".pdf"),
                          )


if __name__ == "__main__":
    main(opts()[0])
