#!/usr/bin/env python

import os, sys


def main(directory):
    roots = []

    assert os.path.isdir(directory)
    for dat in os.listdir(directory):
        if not dat.endswith(".dat"):
            continue

        s = '"file://%s/%s"' % (directory, dat)
        py = "%s/%s" % (directory, dat.replace(".dat", ".py"))
        root = "%s/%s" % (directory, dat.replace(".dat", ".root"))
        roots.append(root)

        cmd = "cat template_datToRoot_cfg.py | sed s@FILEFLAG@'%s'@ | sed s@OUTFLAG@'%s'@ > %s" % (s, '"%s"' % root, py)
        # print cmd
        os.system(cmd)
        os.system("cmsRun %s |& grep -v 'Initiating request to open file' |& grep -v 'Closed file'" % py)

    hadd(directory, roots)


def hadd(directory, roots):
    while directory.endswith("/"):
        directory = directory[:-1]
    cmd = "hadd -f %s.root %s" % (os.path.basename(directory), " ".join(roots))
    # print cmd
    os.system(cmd)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Please provide a directory as an argument.")
    main(sys.argv[1])
