#!/usr/bin/env python

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
        options.noPlot = True

        if not look.main(options, [run], quiet=True):
            roots.append(options.outputFile)
            feds1s.append(fedList(options.feds1))
            feds2s.append(fedList(options.feds2))

    plot(roots, feds1s, feds2s)


def plot(roots, feds1s, feds2s):
    graphs.makeSummaryPdfMulti(inputFiles=roots,
                               feds1s=feds1s,
                               feds2s=feds2s,
                               pdf="output/grs.pdf",
                               onePageOnly=True,
                               )


def runs(**_):
    return [239895,
            240189,
            # 240190,
            # 240193,
            # 240198,
            # 240200,
            240201,
            # 240209,
            # 240212,
            240214,
            # 240216,
        #     240217,
        #     240219,
        #     240223,
        #     240224,
        #     240226,
        #     240229,
        #     240230,
        #     240257,
        #     240259,
        #     240262,
        #     240267,
        #     240272,
        #     240274,
        #     240275,
        #     240278,
        #     240280,
        #     240285,
        #     240466,
            240858,
            240860,
            240862,
            ]


if __name__ == "__main__":
    main(opts()[0], runs(minumum=240189, maximum=240209))
