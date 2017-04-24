#!/usr/bin/env python

import analyze
import printer
import graphs
import sys
from configuration import matching
from configuration.sw import fedList
from options import oparser


def subset(options, l, process=False, invert=False):
    assert not (process and invert)

    out = {}
    for item in l:
        value = getattr(options, item)
        if process:
            out[item] = fedList(value)
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
    if options.file2 and not options.feds2:
        sys.exit("--file2 requires --feds2")
    if 0 <= options.sparseLoop:
        if options.file2:
            sys.exit("--sparse-loop does not work with --file2")
        if options.nEventsSkip:
            sys.exit("--sparse-loop does not work with --nevents-skip")

    matching.__okErrF = fedList(options.okErrF)
    matching.__utcaBcnDelta = options.utcaBcnDelta
    matching.__utcaPipelineDelta = options.utcaPipelineDelta
    printer.__color = not options.noColor

    common = subset(options, ["dump", "nEventsMax", "nEventsSkip", "progress", "sparseLoop"])
    common.update(subset(options, ["noUnpack", "noWarnQuality", "noWarnUnpack"], invert=True))
    common["crateslots"] = fedList(options.crateslots)

    plugins = options.plugins.split(",")
    if 1 <= options.dump and "printraw" not in plugins:
        plugins.append("printraw")
    common["plugins"] = plugins

    outer = {"fedIds": fedList(options.feds1),
             "label": "files1",
             "fileNames": options.file1}
    outer.update(common)

    inner = {}
    if options.feds2:
        inner = {"fedIds": fedList(options.feds2),
                 "label": "files2",
                 "fileNames": options.file2 if options.file2 else options.file1}
        inner.update(common)

    return {"outer": outer,
            "inner": inner,
            "outputFile": options.outputFile,
            "mapOptions": subset(options, ["printEventMap", "identityMap"]),
            "options": subset(options, ["anyEmap", "printEmap", "printMismatches", "fewerHistos"])}


def main(options):
    kargs = processed(options)

    if options.noLoop:
        retCode = 0
        feds1 = kargs["outer"]["fedIds"]
        feds2 = kargs["inner"].get("fedIds", [])
    elif options.profile:
        import cProfile
        cProfile.runctx("analyze.go(**kargs)", globals(), locals(), sort="time")
        # FIXME:
        retCode = 0
        feds1 = []
        feds2 = []
    else:
        retCode, feds1, feds2 = analyze.go(**kargs)

    if feds2 and 0 <= options.dump:
        analyze.printChannelSummary(options.outputFile)

    if not options.noPlot:
        graphs.main(options.outputFile, feds1, feds2)

    return retCode, feds1, feds2


if __name__ == "__main__":
    main(oparser().parse_args()[0])
