#!/usr/bin/env python

import cProfile
import analyze, graphs
from configuration.sw import fedList
from options import oparser


def main(options):
    if options.noLoop:
        retCode = 0
        feds1 = fedList(options.feds1)
        feds2 = fedList(options.feds2)
    elif options.profile:
        pr = cProfile.Profile()
        retCode, feds1, feds2 = pr.runcall(analyze.main, options)
        pr.print_stats("time")
    else:
        retCode, feds1, feds2 = analyze.main(options)

    if feds2 and 0 <= options.dump:
        analyze.printChannelSummary(options.outputFile)

    if not options.noPlot:
        graphs.main(options.outputFile, feds1, feds2)

    return retCode, feds1, feds2


if __name__ == "__main__":
    main(oparser().parse_args()[0])
