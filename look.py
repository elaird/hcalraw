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

    for d in ["/afs/cern.ch/project/eos/installation", os.environ["HOME"]]:
        f = "%s/0.3.84-aquamarine/bin/eos.select" % d
        if os.path.exists(f):
            return f

    sys.exit("ERROR: could not find eos.")


def find(i, run, index, onward):
    return eval("find%d" % i)(run, index, onward)


def find1(run, _, __):
    for local in ["tmp/USC_%d.root" % run, "data/USC_%d.root" % run]:
        if os.path.exists(local):
            return local, "v2"


def find2(run, _, __):
    LS1 = "/store/group/dpg_hcal/comm_hcal/LS1/USC_%d.root" % run
    stat = "%s stat %s" % (eos(), LS1)
    if not utils.commandOutputFull(stat)["returncode"]:
        return "%s/%s" % (eosprefix, LS1), "v2"


def find3(run, index, onward):
    return find_gr(run, "/store/data/Commissioning2015/HcalNZS/RAW/v1", index, onward)


def find4(run, index, onward):
    return find_gr(run, "/store/data/Commissioning2015/Cosmics/RAW/v1", index, onward)


def find5(run, index, onward):
    return find_gr(run, "/store/data/Commissioning2015/MinimumBias/RAW/v1", index, onward)


def find6(run, index, onward):
    return find_gr(run, "/store/express/Commissioning2015/ExpressCosmics/FEVT/Express-v1", index, onward)


def find_gr(run, grdir, index=None, onward=False):
    d = "%s/000/%03d/%03d/00000/" % (grdir, run/1000, run % 1000)
    stat = "%s stat %s" % (eos(), d)
    ls = stat.replace(" stat ", " ls -l ")

    if utils.commandOutputFull(stat)["returncode"]:
        return

    listings = filter(lambda x: x, utils.commandOutputFull(ls)["stdout"].split("\n"))

    month_num = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr":  4, "May":  5, "Jun":  6,
                 "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

    coords = []
    for listing in listings:
        fields = listing.split()
        month, day, hhmm, fileName = fields[-4:]
        hh, mm = hhmm.split(":")
        coords.append((month_num[month], int(day), int(hh), int(mm), fileName))

    coords.sort()
    if index and abs(index) < len(coords):
        if onward:
            coords = coords[index:]
        else:
            coords = [coords[index]]
        for c in coords:
            print c

    files = [c[-1] for c in coords]
    if files:
        l = ",".join(["%s/%s%s" % (eosprefix, d, f) for f in files])
        return l, "v3"


def report(file1):
    fileNames = file1.split(",")
    pieces = [f.split("/") for f in fileNames]
    bases = set(["/".join(piece[:-1]) for piece in pieces])
    assert len(bases) == 1, bases
    msg = "matching file" if len(fileNames) == 1 else "files"
    print "Found %d %s in %s/" % (len(fileNames), msg, "/".join(bases))


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

    if options.noLoop:  # skip file finding
        options.file1 = "dummy"
        oneRun.main(options)
        return

    for iFind in range(1, 7):
        ret = find(iFind, run, options.index, options.onward)
        if not ret:
            continue

        options.file1, match = ret
        if not options.match:
            options.match = match

        report(options.file1)
        oneRun.main(options)
        return

    sys.exit("Did not find a matching file for run %d.  Perhaps try 'source env/lxplus6.sh'" % run)


if __name__ == "__main__":
    eosprefix = "root://eoscms.cern.ch/"
    main(*opts(alsoArgs=True))
