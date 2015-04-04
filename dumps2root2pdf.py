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


def rooted(dats=[], options=None):
    feds = {}

    prefixes = []
    for dat in dats:
        prefix, fed, root1, root2, cmd = command(dat)
        prefixes.append(prefix)
        feds[fed] = (root1, root2)

        print "%s %4d: %s" % (prefix, fed, root1)
        # print cmd; continue
        os.system(cmd)

    return sorted(list(prefixes))[0], feds


def toCompare(feds, split1, split2):
    if split1 in feds:
        return filter(lambda x: x in feds, split2)
    else:
        return []


def histogrammed(prefix, feds, split=1118):
    roots = []
    feds1s = []
    feds2s = []

    comp = toCompare(feds, split, [718, 719])
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
                feds1s.append([cfed])
                feds2s.append([fed])
                oneRun.main(options)

        else:
            print "solo %4d:" % fed
            options.feds1 = str(fed)
            options.file1 = root1
            options.outputFile = rootOut

            options.feds2 = ""
            options.file2 = ""

            roots.append(options.outputFile)
            feds1s.append([fed])
            feds2s.append([])
            oneRun.main(options)

    return prefix, roots, feds1s, feds2s


def plot(prefix, roots, feds1s, feds2s):
    graphs.makeSummaryPdfMulti(inputFiles=roots,
                               feds1s=feds1s,
                               feds2s=feds2s,
                               pdf="output/%s.pdf" % prefix,
                               )


if __name__ == "__main__":
    options, args = opts(alsoArgs=True)
    plot(*histogrammed(*rooted(args, options)))
