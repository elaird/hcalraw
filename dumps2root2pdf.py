#!/usr/bin/env python

import os
import sys
import graphs
import oneRun
from options import opts


def bail(dat, fields, tag):
    sys.exit("skipping %s (reason %s: %s)" % (dat, tag, str(fields)))


def command(dat):
    __feds = {22: 1118,
              29: 1120,
              32: 1122,
              718: 718,
              719: 719,
              }

    fields = dat.split("_")
    if len(fields) != 3:
        bail(dat, fields, "a")

    prefix2, crate, suffix = fields
    if suffix not in [".txt", ".dat", "mb.txt", "mb.dat"]:
        bail(dat, fields, "b")

    try:
        crate = int(crate)
        if crate not in __feds:
            bail(dat, fields, "c")
    except ValueError:
        bail(dat, fields, "d")

    prefix = prefix2[1 + prefix2.rfind("/"):]
    fed = __feds[crate]
    print prefix, fed

    tag = "deadbeef" if fed < 1000 else "badcoffee"

    root1 = "data/%s_%s_%d.root" % (tag, prefix, fed)
    root2 = root1.replace("data/%s_" % tag, "output/")

    cmd = " && ".join(["cat %s | cpp/%s %s" % (dat, tag, fed),
                       "mv %s%d.root %s" % (tag, fed, root1),
                   ])

    return prefix, fed, root1, root2, cmd


def looped(dats=[], options=None):
    prefixes = []
    feds = []
    roots = []
    
    for dat in dats:
        prefix, fed, root1, root2, cmd = command(dat)
        prefixes.append(prefix)
        feds.append(fed)
        roots.append(root2)

        # print cmd; continue
        os.system(cmd)

        options.file1 = root1
        options.feds1 = str(fed)
        options.outputFile = root2
        oneRun.main(options)

    return prefixes, feds, roots


def plot(prefixes, feds, roots):
    graphs.makeSummaryPdf(inputFiles=roots,
                          feds1=feds,
                          pdf="output/%s.pdf" % sorted(list(prefixes))[0]
                          )


if __name__ == "__main__":
    options, args = opts(alsoArgs=True)
    plot(*looped(args, options))
