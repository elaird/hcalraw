#!/usr/bin/env python

import sys
import graphs
import look
from options import opts
from configuration.sw import fedList


def main(options, runs=[]):
    roots = []
    feds1s = []
    feds2s = []
    for run in runs:
        if run == 239895:
            options.hhmm = 2212
        else:
            options.hhmm = None

        options.file1 = ""
        options.file2 = ""

        if not look.main(options, [run], quiet=True):
            roots.append(options.outputFile)
            feds1s.append(fedList(options.feds1))
            feds2s.append(fedList(options.feds2))

    plot(roots, feds1s, feds2s)


def plot(roots, feds1s, feds2s):
    for i, stem in enumerate(["overview", "vs", "maps_counts", "maps_rates", "orbit", "evn", "orn", "trends"]):
        graphs.makeSummaryPdfMulti(inputFiles=roots,
                                   feds1s=feds1s,
                                   feds2s=feds2s,
                                   pdf="output/%s.pdf" % stem,
                                   pages=[1 + i],
                                  )


def runs(file=None):
    out = []
    for i, lineRaw in enumerate(file):
        line = lineRaw.strip()
        if line.startswith("#"):
            continue
        try:
            out.append(int(line))
        except ValueError:
            print "skipping line %d: '%s'" % (i, line)
    return out


if __name__ == "__main__":
    main(opts()[0], runs(sys.stdin))
