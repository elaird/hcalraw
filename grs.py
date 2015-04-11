#!/usr/bin/env python

import os
import graphs
from look import eos


def main(runs=[]):
    roots = []
    feds1s = []
    feds2s = []
    for run in runs:
        os.system("./look.py %d" % run)
        roots.append("output/%d.root" % run)
        feds1s.append([718, 719])
        feds2s.append([1118, 1120, 1122])

    graphs.makeSummaryPdfMulti(inputFiles=roots,
                               feds1s=feds1s,
                               feds2s=feds2s,
                               pdf="output/gr.pdf",
                               onePageOnly=True,
                               )


def runs(**_):
    return [240189,
            240190,
            240193,
            240198,
            240200,
            240201,
            240209,
        ]


if __name__ == "__main__":
    main(runs(minumum=240189, maximum=240209))
