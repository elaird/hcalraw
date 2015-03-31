#!/usr/bin/env python

import os
import sys
import utils
import oneRun
from options import opts


def main(options, args):
    if len(args) != 1:
        sys.exit("Please provide a run number as the argument.")
    try:
        run = int(args[0])
    except ValueError:
        sys.exit("Could not convert %s to int." % args[0])

    options.feds1 = "718,719"
    options.feds2 = "uHF"
    options.dump = 0
    options.progress = True
    options.outputFile = "output/%d.root" % run
    if not options.nEvents:
        options.nEvents = 10

    local1 = "data/USC_%d.root" % run
    local2 = "%s/USC_%d.root" % (os.environ.get("LS1", ""), run)
    gdir1 = "%s/Cosmics/RAW/v1/000/%d/%d/00000/" % (os.environ.get("GR2", ""), run/1000, run % 1000)
    eos = "/afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select"
    stem = "root://eoscms.cern.ch/"

    if os.path.exists(local1):
        options.file1 = local1
        options.match = "v2"
    elif not utils.commandOutputFull("%s stat %s" % (eos, local2.replace(stem, "")))["returncode"]:
        options.file1 = local2
        options.match = "v2"
    elif not utils.commandOutputFull("%s stat %s" % (eos, gdir1.replace(stem, "")))["returncode"]:
        options.match = "v4"
        files = utils.commandOutputFull("%s ls %s" % (eos, gdir1.replace(stem, "")))["stdout"].split("\n")
        print files
        # global --file1=$GR2/Cosmics/RAW/v1/000/239/201/00000/0012EAD3-77D6-E411-8052-02163E01351E.root
    else:
        sys.exit("Did not find a matching file.  Perhaps try 'source env/lxplus6.sh'")

    if options.file1:
        oneRun.main(options)



if __name__ == "__main__":
    main(*opts(alsoArgs=True))
