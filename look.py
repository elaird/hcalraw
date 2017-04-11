#!/usr/bin/env python

import optparse, os, sys
import oneRun, utils
from options import oparser
from configuration import sw


def this_machine(run):
    out = []
    for filename in sw.files_this_machine(run):
        if os.path.exists(filename):
            out.append(filename)
    return out


def local_eos(run):
    out = []
    for filename in sw.files_eos_local(run):
        shortName = filename[filename.find("/store"):]
        if not utils.commandOutputFull("eos stat %s" % shortName)["returncode"]:
            out.append(filename)
    return out


def find_gr(run, grdir, hhmmMin=None, quiet=False):
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
    if hhmmMin:
        mmMin = hhmmMin % 100
        hhMin = hhmmMin / 100
        coords = filter(lambda x: hhMin < x[2] or (hhMin == x[2] and mmMin <= x[3]), coords)
        if not quiet:
            for c in coords:
                print c

    files = [c[-1] for c in coords]
    if files:
        l = ",".join(["%s/%s%s" % (sw.eosprefix, d, f) for f in files])
        return l


def report(fileNames, iFind):
    pieces = [f.split("/") for f in fileNames]
    bases = set(["/".join(piece[:-1]) for piece in pieces])
    assert len(bases) == 1, bases
    if len(fileNames) == 1 and iFind <= 2:
        print "Found matching file: %s" % fileNames[0]
    else:
        print "Found %4d file(s) in %s/" % (len(fileNames), "/".join(bases))


def override(options, run):
    options.outputFile = "output/%d.root" % run
    if not options.nEvents:
        options.nEvents = 4

    if not options.quiet:
        options.progress = True
        if options.dump == -1:
            options.dump = 0

    if options.noLoop:  # skip file finding
        options.file1 = "dummy"
        oneRun.main(options)
        sys.exit()


def opts():
    parser = oparser(arg="RUN_NUMBER")

    look = optparse.OptionGroup(parser, "Options solely for use with look.py")
    look.add_option("--quiet",
                    dest="quiet",
                    default=False,
                    action="store_true",
                    help="Print less to stdout")
    look.add_option("--hhmm",
                    dest="hhmm",
                    default=None,
                    type="int",
                    help="minimum hhmm")
    parser.add_option_group(look)

    options, args = parser.parse_args()

    if len(args) != 1:
        sys.exit("Please provide a run number as the argument.")
    try:
        run = int(args[0])
    except ValueError:
        sys.exit("Could not convert %s to int." % args[0])

    override(options, run)
    return options, run


def search(run):
    global_xrd = this_machine
    for search_func in [this_machine, local_eos, global_xrd]:
        files = search_func(run)
        # options.file1 = find_gr(run, grDir, options.hhmm, quiet)
        if files:
            return files


def main():
    options, run = opts()

    files = search(run)
    if not files:
        sys.exit("Did not find a matching file for run %d." % run)

    if 2 <= len(files):
        fileNames = files.split(",")
        n = len(fileNames)
        if 2 <= n and options.hhmm is None:
            options.sparseLoop = max(1, options.nEvents / n)
        else:
            options.sparseLoop = -1
        # report(fileNames, iFind)
    else:
        options.file1 = files[0]
        if "B904" in options.file1 and options.feds1 == "HCAL":
            options.feds1 = "B904"

    oneRun.main(options)


if __name__ == "__main__":
    main()
