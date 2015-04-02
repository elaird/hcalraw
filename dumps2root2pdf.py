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

    tag = "deadbeef" if fed < 1000 else "badcoffee"

    root1 = "data/%s_%s_%d.root" % (tag, prefix, fed)
    root2 = root1.replace("data/%s_" % tag, "output/")

    cmd = " && ".join(["cat %s | cpp/%s %s" % (dat, tag, fed),
                       "mv %s%d.root %s" % (tag, fed, root1),
                   ])

    return prefix, fed, root1, root2, cmd


def rooted(dats=[], options=None, split=1118):
    feds = {}

    prefixes = []
    for dat in dats:
        prefix, fed, root1, root2, cmd = command(dat)
        prefixes.append(prefix)
        feds[fed] = (root1, root2)

        print "%s %4d: %s" % (prefix, fed, root1)
        # print cmd; continue
        os.system(cmd)

    comp = []
    if split in feds:
        for i in [718, 719]:
            if i in feds:
                comp.append(i)

    return sorted(list(prefixes))[0], feds, comp, split


def histogrammed(prefix, feds, comp, split):
    roots = []

    for fed, (root1, rootOut) in sorted(feds.iteritems()):
        if fed in comp:
            continue

        if comp and fed == split:
            for cfed in comp:
                print "comparison of %4d to %4d:" % (cfed, fed)
                options.feds1 = str(cfed)
                options.file1 = feds[cfed][0]
                options.outputFile = feds[cfed][1]

                options.file2 = root1
                options.feds2 = str(fed)

                roots.append(options.outputFile)
                oneRun.main(options)

        else:
            print "solo %4d:" % fed
            options.feds1 = str(fed)
            options.file1 = root1
            options.outputFile = rootOut

            options.feds2 = ""
            options.file2 = ""

            roots.append(options.outputFile)
            oneRun.main(options)

    return prefix, sorted(feds.keys()), roots


def plot(prefix, fedList, roots):
    graphs.makeSummaryPdf(inputFiles=roots,
                          feds1=fedList,
                          pdf="output/%s.pdf" % prefix,
                          )


if __name__ == "__main__":
    options, args = opts(alsoArgs=True)
    plot(*histogrammed(*rooted(args, options)))
