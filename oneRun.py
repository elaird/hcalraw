#!/usr/bin/env python

import analyze
import configuration
import printer
import graphs
import sys
from options import opts


def subset(options, l, process=False):
    out = {}
    for item in l:
        out[item] = getattr(options, item)
        if process:
            out[item] = configuration.fedList(out[item])
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
    kargs.update(subset(options, ["file1", "file2", "nEvents", "nEventsSkip", "outputFile", "noUnpack"]))

    kargs["patternMode"] = subset(options, ["rmRibbon", "nTs", "patternB"]) if options.patterns else None
    kargs["compareOptions"] = subset(options, ["adcPlots", "anyEmap", "printEmap"])
    kargs["mapOptions"] = subset(options, ["printEventMap", "identityMap"])
    kargs["printOptions"] = subset(options, ["dump", "progress"])
    kargs["printOptions"]["warn"] = not options.noWarnUnpack
    kargs["printOptions"]["crateslots"] = configuration.fedList(options.crateslots)

    analyze.oneRun(**kargs)


def main(options):
    check(options)

    if options.match:
        configuration.matchRange = getattr(configuration, "matchRange_%s" % options.match)
        configuration.matchRange()  # call once to set utcaBcnDelta

    if options.noColor:
        printer.__color = False

    if not options.noLoop:
        analyze.setup()
        if options.profile:
            import cProfile
            cProfile.runctx("go(options)", globals(), locals(), sort="time")
        else:
            go(options)

    graphs.makeSummaryPdf(inputFiles=[options.outputFile],
                          feds1=configuration.fedList(options.feds1),
                          feds2=configuration.fedList(options.feds2),
                          pdf=options.outputFile.replace(".root", ".pdf"),
                          )


if __name__ == "__main__":
    main(opts()[0])
