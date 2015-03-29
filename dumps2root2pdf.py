#!/usr/bin/env python

import os
import sys
import oneRun


def bail(dat, fields, tag):
    sys.exit("skipping %s (reason %s: %s)" % (dat, tag, str(fields)))


def command(dat):
    __feds = {22: 1118,
              29: 1120,
              32: 1122,
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

    root1 = "data/badcoffee_%s_%d.root" % (prefix, fed)
    root2 = root1.replace("data/badcoffee_", "output/")

    cmd = " && ".join(["cat %s | cpp/badcoffee %s" % (dat, fed),
                       "mv badcoffee%d.root %s" % (fed, root1),
                   ])

    return prefix, fed, root1, root2, cmd


def looped(dats=[], options=None):
    prefixes = []
    feds = []
    roots = []
    
    for dat in dats:
        prefix, fed, root1, root2, cmd = command(dat)
        options.file1 = root1
        options.feds1 = str(fed)
        options.outputFile = root2

        prefixes.append(prefix)
        feds.append(fed)
        roots.append(root2)
        # print cmd
        os.system(cmd)
        oneRun.main(options)

    return prefixes, feds, roots


def plot(prefixes, feds, roots):
    if len(set(prefixes)) != 1:
        return

    rootFile = "output/%s.root" % prefixes[0]
    # cmd = "hadd -f %s %s" % (rootFile, " ".join(roots))
    # print cmd
    # os.system(cmd)

    import graphs
    graphs.makeSummaryPdf(inputFiles=roots,
                          feds1=feds,
                          pdf=rootFile.replace(".root", ".pdf"),
                          )


if __name__ == "__main__":
    from options import opts
    options, args = opts(alsoArgs=True)
    plot(*looped(args, options))
