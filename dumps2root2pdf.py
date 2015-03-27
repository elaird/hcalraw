#!/usr/bin/env python

import os
import sys
import graphs


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
    opts = " --".join(["", "progress", "no-warn-unpack", "nevents=100"][:-1])

    cmds = ["cat %s | bin/badcoffee %s" % (dat, fed),
            "mv badcoffee%d.root %s" % (fed, root1),
            "./oneRun.py --file1=%s --feds1=%d --output-file=%s %s" % (root1, fed, root2, opts)
            ]
    return prefix, fed, root2, " && ".join(cmds)


def looped(dats=[]):
    prefixes = []
    feds = []
    roots = []
    
    for dat in dats:
        prefix, fed, root2, cmd = command(dat)
        prefixes.append(prefix)
        feds.append(fed)
        roots.append(root2)
        # print cmd
        os.system(cmd)

    return prefixes, feds, roots


def plot(prefixes, feds, roots):
    if len(set(prefixes)) != 1:
        return

    rootFile = "output/%s.root" % prefixes[0]
    # cmd = "hadd -f %s %s" % (rootFile, " ".join(roots))
    # print cmd
    # os.system(cmd)

    graphs.makeSummaryPdf(inputFiles=roots,
                          feds1=feds,
                          pdf=rootFile.replace(".root", ".pdf"),
                          )

if __name__ == "__main__":
    plot(*looped(sys.argv[1:]))
