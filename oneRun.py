#!/usr/bin/env python

import analyze
import printer
import graphs
import sys
from configuration import sw, matching
from options import oparser


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


def processed(options):
    if not all([options.file1, options.feds1]):
        sys.exit("--file1 and --feds1 are required (see './oneRun.py --help').")
    if not options.outputFile.endswith(".root"):
        sys.exit("--output-file must end with .root (%s)" % options.outputFile)
    if 0 <= options.sparseLoop:
        if options.file2:
            sys.exit("--sparse-loop does not work with --file2")
        if options.nEventsSkip:
            sys.exit("--sparse-loop does not work with --nevents-skip")

    matching.__okErrF = sw.fedList(options.okErrF)
    matching.__utcaBcnDelta = options.utcaBcnDelta
    matching.__utcaPipelineDelta = options.utcaPipelineDelta
    printer.__color = not options.noColor

    kargs = subset(options, ["feds1", "feds2"], process=True)
    kargs.update(subset(options, ["nEvents", "nEventsSkip", "outputFile", "noUnpack", "sparseLoop", "plugins"]))
    kargs["compareOptions"] = subset(options, ["anyEmap", "printEmap", "printMismatches", "fewerHistos"])
    kargs["mapOptions"] = subset(options, ["printEventMap", "identityMap"])
    kargs["printOptions"] = subset(options, ["dump", "progress"])
    kargs["printOptions"].update(subset(options, ["noWarnUnpack", "noWarnQuality"], invert=True))
    kargs["printOptions"].update(subset(options, ["crateslots"], process=True))

    for iFile in [1, 2]:
        value = getattr(options, "file%d" % iFile)
        if value:
            kargs["files%d" % iFile] = value.split(",")

    if kargs["feds2"] and not kargs.get("files2"):
        kargs["files2"] = kargs["files1"]
        kargs["mapOptions"]["identityMap"] = True

    kargs["plugins"] = options.plugins.split(",")
    if 1 <= options.dump and "printraw" not in kargs["plugins"]:
        kargs["plugins"].append("printraw")

    return kargs


def main(options):
    kargs = processed(options)
    analyze.setup(kargs["plugins"])

    retCode = 0
    feds1 = kargs["feds1"]
    feds2 = kargs["feds2"]

    if options.noLoop:
        pass
    elif options.profile:
        import cProfile
        cProfile.runctx("analyze.oneRun(**kargs)", globals(), locals(), sort="time")
        # FIXME: retCode, feds1, feds2
    else:
        retCode, feds1, feds2 = analyze.oneRun(**kargs)

    if feds2 and 0 <= options.dump:
        analyze.printChannelSummary(options.outputFile)

    if not options.noPlot:
        graphs.main(options.outputFile, feds1, feds2)

    return retCode, feds1, feds2


if __name__ == "__main__":
    main(oparser().parse_args()[0])
