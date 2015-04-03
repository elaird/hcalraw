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
    options.progress = True
    options.outputFile = "output/%d.root" % run

    # override three defaults: nEvents, dump, match
    if not options.nEvents:
        options.nEvents = 10

    if options.dump == -1:
        options.dump = 0

    stem = "root://eoscms.cern.ch/"
    LS1 = "%s/store/group/dpg_hcal/comm_hcal/LS1" % stem
    GR2 = "%s/store/data/Commissioning2015" % stem

    local1 = "data/USC_%d.root" % run
    local2 = "%s/USC_%d.root" % (LS1, run)
    gdir1 = "%s/Cosmics/RAW/v1/000/%3d/%3d/00000/" % (GR2, run/1000, run % 1000)

    eos = None
    #################################
    # NOTES from local installation #
    #################################
    # rsync -av lxplus.cern.ch:/afs/cern.ch/project/eos/installation/0.3.84-aquamarine .
    # emerge -av readline:5
    # /usr/lib # ln -s libcrypto.so libcrypto.so.6
    # edit 0.3.84-aquamarine/bin/eos.select :
    # export EOSSYS=${HOME}/0.3.84-aquamarine
    # export EOS_MGM_URL=root://eoscms.cern.ch
    ################################################
    for _eos in ["eos",
                 "%s/0.3.84-aquamarine/bin/eos.select" % "/afs/cern.ch/project/eos/installation",
                 "%s/0.3.84-aquamarine/bin/eos.select" % os.environ["HOME"],
                 ]:
        if not os.path.exists(_eos):
            continue
        else:
            eos = _eos
            break

    if eos is None:
        sys.exit("ERROR: could not find eos.")

    if os.path.exists(local1):
        options.file1 = local1
        if not options.match:
            options.match = "v2"
    elif not utils.commandOutputFull("%s stat %s" % (eos, local2.replace(stem, "")))["returncode"]:
        options.file1 = local2
        if not options.match:
            options.match = "v2"
    elif not utils.commandOutputFull("%s stat %s" % (eos, gdir1.replace(stem, "")))["returncode"]:
        files = utils.commandOutputFull("%s ls %s" % (eos, gdir1.replace(stem, "")))["stdout"].split("\n")
        if files:
            options.file1 = "%s/%s" % (gdir1, files[0])
        if not options.match:
            options.match = "v4"

    if options.file1:
        oneRun.main(options)
    else:
        sys.exit("Did not find a matching file for run %d.  Perhaps try 'source env/lxplus6.sh'" % run)


if __name__ == "__main__":
    main(*opts(alsoArgs=True))
