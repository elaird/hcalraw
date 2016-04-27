#!/usr/bin/env python

import analyze
import printer
import graphs
import sys
from configuration import sw, matching
from options import opts


def subset(options, l, process=False, invert=False):
    assert not (process and invert)

    out = {}
    for item in l:
        value = getattr(options, item)
        if process:
            out[item] = sw.fedList(value)
        elif invert:
            # "noFoo": True --> "foo": False
            out[item[2].lower() + item[3:]] = not value
        else:
            out[item] = value
    return out


def check_and_adjust(options):
    if not all([options.file1, options.feds1]):
        sys.exit("--file1 and --feds1 are required (see './oneRun.py --help').")
    if not options.outputFile.endswith(".root"):
        sys.exit("--output-file must end with .root (%s)" % options.outputFile)
    if 0 <= options.sparseLoop:
        if options.file2:
            sys.exit("--sparse-loop does not work with --file2")
        if options.nEventsSkip:
            sys.exit("--sparse-loop does not work with --nevents-skip")
    if options.feds2 and (not options.file2) and (not options.noLoop):
        # print "INFO: using --file1 also for --file2; also using identity map"
        options.file2 = options.file1
        options.identityMap = True

    if options.patterns:
        printer.info("setting nEvents=1 (--patterns was passed)")
        options.nEvents = 1


def go(options):
    kargs = subset(options, ["feds1", "feds2"], process=True)
    kargs.update(subset(options, ["nEvents", "nEventsSkip", "outputFile", "noUnpack", "patterns", "sparseLoop"]))
    kargs["compareOptions"] = subset(options, ["anyEmap", "printEmap", "printMismatches", "fewerHistos"])
    kargs["mapOptions"] = subset(options, ["printEventMap", "identityMap"])
    kargs["printOptions"] = subset(options, ["dump", "progress"])
    kargs["printOptions"].update(subset(options, ["noWarnUnpack", "noWarnQuality"], invert=True))
    kargs["printOptions"]["crateslots"] = sw.fedList(options.crateslots)

    for iFile in [1, 2]:
        value = getattr(options, "file%d" % iFile)
        if value:
            kargs["files%d" % iFile] = value.split(",")

    return analyze.oneRun(**kargs)


def main(options):
    check_and_adjust(options)

    matching.__okErrF = sw.fedList(options.okErrF)
    matching.__utcaBcnDelta = options.utcaBcnDelta
    matching.__utcaPipelineDelta = options.utcaPipelineDelta
    if options.noColor:
        printer.__color = False

    if options.noLoop:
        goCode = 0
    else:
        analyze.setup()
        if options.profile:
            import cProfile
            cProfile.runctx("go(options)", globals(), locals(), sort="time")
            goCode = 0  # FIXME
        else:
            goCode = go(options)

    if options.feds2 and 0 <= options.dump:
        analyze.printChannelSummary(options.outputFile)

    if not options.noPlot:
        graphs.main(options)

    return goCode


if __name__ == "__main__":
    main(opts()[0])
