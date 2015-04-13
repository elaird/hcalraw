#!/usr/bin/env python

import os
import graphs
import look
from options import opts


def main(runs=[]):
    roots = []
    feds1s = []
    feds2s = []
    for run in runs:
        args = "%d --nevents=10" % run
        if run == 239895:
            args += " --hhmm=2212"

        os.system("./look.py %s" % args)
        roots.append("output/%d.root" % run)
        feds1s.append([718, 719])
        feds2s.append([1118, 1120, 1122])

    graphs.makeSummaryPdfMulti(inputFiles=roots,
                               feds1s=feds1s,
                               feds2s=feds2s,
                               pdf="output/grs.pdf",
                               onePageOnly=True,
                               )


def runs(**_):
    return [239895,
            240189,
            240190,
            240193,
            240198,
            240200,
            240201,
            240209,
            240212,
            240214,
            240216,
            240217,
            240219,
            240223,
            240224,
            240226,
            240229,
            240230,
            240257,
            240259,
            240262,
            240267,
            240272,
            240274,
            240275,
            240278,
            240280,
            240285,
        ]


if __name__ == "__main__":
    main(runs(minumum=240189, maximum=240209))
