#!/usr/bin/env python


import analyze
import configuration
import printer
import sys
import cProfile
import graphs
from options import opts


def main(options):
    if options.match:
        configuration.matchRange = getattr(configuration, "matchRange_%s" % options.match)
        configuration.matchRange()  # call once to set utcaBcnDelta

    if options.noColor:
        printer.__color = False

    compareOptions = {}
    for item in ["adcPlots", "anyEmap", "printEmap"]:
        compareOptions[item] = getattr(options, item)

    patternOptions = {"rmRibbon": options.rmRibbon,
                      "nTs": options.nts,
                      "pureFibersOnly": not options.patternB,
                      "active": options.patterns,
                      }

    mapOptions = {}
    for key in ["filterEvn", "printEventMap", "identityMap"]:
        mapOptions[key] = getattr(options, key)

    printOptions = {"dump": options.dump,
                    "warn": not options.noWarnUnpack,
                    "progress": options.progress,
                    "crateslots": configuration.fedList(options.crateslots),
                    }

    feds1 = configuration.fedList(options.feds1)
    feds2 = configuration.fedList(options.feds2)

    def go():
        analyze.oneRun(file1=options.file1,
                       feds1=feds1,
                       file2=options.file2,
                       feds2=feds2,
                       nEvents=options.nevents,
                       nEventsSkip=options.neventsSkip,
                       patternMode=patternOptions,
                       mapOptions=mapOptions,
                       outputFile=options.outputFile,
                       printOptions=printOptions,
                       compareOptions=compareOptions,
                       unpack=not options.noUnpack,
                       unpackSkipFlavors=configuration.fedList(options.unpackSkipFlavors),
                       )

    if not options.noLoop:
        if options.profile:
            cProfile.run("go()", sort="time")
        else:
            go()

    graphs.makeSummaryPdf(inputFiles=[options.outputFile],
                          feds1=feds1,
                          feds2=feds2,
                          pdf=options.outputFile.replace(".root", ".pdf"),
                          scatter=feds2 and not options.anyEmap,
                          )


if __name__ == "__main__":
    main(opts())
