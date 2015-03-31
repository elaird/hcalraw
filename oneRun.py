#!/usr/bin/env python

import analyze
import configuration
import printer
import graphs
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
        sys.exit("--file1 and --feds1 are required.")
    if not options.outputFile.endswith(".root"):
        sys.exit("--output-file must end with .root (%s)" % options.outputFile)
    if options.feds2 and not options.file2:
        print "INFO: using --file1 also for --file2; also using identity map"
        options.file2 = options.file1
        options.identityMap = True


def main(options):
    check(options)

    if options.match:
        configuration.matchRange = getattr(configuration, "matchRange_%s" % options.match)
        configuration.matchRange()  # call once to set utcaBcnDelta

    if options.noColor:
        printer.__color = False

    kargs = subset(options, ["feds1", "feds2", "unpackSkipFlavors"], process=True)
    kargs.update(subset(options, ["file1", "file2", "nEvents", "nEventsSkip", "outputFile", "noUnpack"]))

    kargs["patternMode"] = subset(options, ["rmRibbon", "nTs", "patternB"]) if options.patterns else None
    kargs["compareOptions"] = subset(options, ["adcPlots", "anyEmap", "printEmap"])
    kargs["mapOptions"] = subset(options, ["filterEvn", "printEventMap", "identityMap"])
    kargs["printOptions"] = subset(options, ["dump", "progress"])
    kargs["printOptions"]["warn"] = not options.noWarnUnpack
    kargs["printOptions"]["crateslots"] = configuration.fedList(options.crateslots)

    def go():
        analyze.oneRun(**kargs)

    if not options.noLoop:
        analyze.setup()
        if options.profile:
            import cProfile
            cProfile.run("go()", sort="time")
        else:
            go()

    graphs.makeSummaryPdf(inputFiles=[options.outputFile],
                          feds1=kargs["feds1"],
                          feds2=kargs["feds2"],
                          pdf=options.outputFile.replace(".root", ".pdf"),
                          )


if __name__ == "__main__":
    main(opts()[0])
