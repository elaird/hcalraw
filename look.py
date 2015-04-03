#!/usr/bin/env python

import os
import sys
import utils
import oneRun
from options import opts


def eos():
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
    aq = "0.3.84-aquamarine/bin/eos.select"
    for f in ["eos",
              "%s/%s" % ("/afs/cern.ch/project/eos/installation", aq),
              "%s/%s" % (os.environ["HOME"], aq),
              ]:
        if not os.path.exists(f):
            continue
        else:
            return f

    sys.exit("ERROR: could not find eos.")


def find1(run):
    for local in ["tmp/USC_%d.root" % run, "data/USC_%d.root" % run]:
        if os.path.exists(local):
            return local, "v2"


def find2(run):
    LS1 = "/store/group/dpg_hcal/comm_hcal/LS1/USC_%d.root" % run
    stat = "%s stat %s" % (eos(), LS1)
    if not utils.commandOutputFull(stat)["returncode"]:
        return "%s/%s" % (eosprefix, LS1), "v2"


def find3(run):
    express = "/store/express/Commissioning2015/ExpressCosmics/FEVT/Express-v1"
    express += "/000/%3d/%3d/00000/" % (run/1000, run % 1000)

    stat = "%s stat %s" % (eos(), express)
    ls = stat.replace(" stat ", " ls ")

    if not utils.commandOutputFull(stat)["returncode"]:
        files = filter(lambda x: x, utils.commandOutputFull(ls)["stdout"].split("\n"))
        if files:
            l = ",".join(["%s/%s%s" % (eosprefix, express, f) for f in files])
            return l, "v4"


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

    for func in [find1, find2, find3]:
        ret = func(run)
        if not ret:
            continue

        options.file1, match = ret
        if not options.match:
            options.match = match

        oneRun.main(options)
        return

    sys.exit("Did not find a matching file for run %d.  Perhaps try 'source env/lxplus6.sh'" % run)


if __name__ == "__main__":
    eosprefix = "root://eoscms.cern.ch/"
    main(*opts(alsoArgs=True))
