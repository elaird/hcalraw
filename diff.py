#!/usr/bin/env python

from configuration import patterns as conf
import optparse
import sys


def mapping(file=None, skip=[]):
    out = {}
    misc = []
    for line in file:
        if any([item in line for item in skip]):
            continue

        if line.startswith(conf.lineStart):
            fields = line.split(":")
            if len(fields) <= 1:
                sys.exit("Problem processing this line (length %d < 2):\n%s" % (len(fields), line))
            else:
                be = fields[0].replace(conf.lineStart, "").split()
                be = (be[0], int(be[1]), int(be[2]))
                fe = " ".join(fields[1:])

            out[be] = tuple(fe.split())
        elif line != "\n":
            misc.append(line)
    return out, misc


def diffs(ref={}, cabled={}):
    extra = {}
    missing = {}
    different = {}
    same = {}
    for be, fe in sorted(ref.iteritems()):
        if be not in cabled:
            missing[be] = fe
            continue

        if fe != cabled[be]:
            different[be] = (fe, cabled[be])
        else:
            same[be] = fe

    for be, fe in cabled.iteritems():
        if be not in ref:
            extra[be] = fe

    return extra, missing, different, same


def pretty(be=None, fe=None):
    if be:
        dcc, sp, fi = be
        if dcc.startswith("u"):
            crate = dcc[1:]
            slot = sp
            s = "    %2s     %2s   %2s:  " % (crate, slot, fi)
        else:
            crate = conf.expectedCrate(int(dcc))
            exp = conf.expectedHtr(int(dcc), int(sp))
            htr = "%2d%1s" % (exp["Slot"], exp["Top"])
            s = "%2s(%2d) %2s(%3s) %2s:  " % (dcc, crate, sp, htr, fi)
    else:
        s = ""

    try:
        s += " %6s %2s %2s" % fe
    except TypeError:
        s += " ".join(fe)
    return s


def fiberCount(feCoords=[]):
    out = {}
    for coords in feCoords:
        rbx = coords[0]
        if rbx in out:
            out[rbx] += 1
        else:
            out[rbx] = 1
    return out


def printTable(rbxes={}, header="", zero="  "):
    if header:
        header = "| %s |" % header
        print "-"*len(header)
        print header
        print "-"*len(header)

    rbxList = conf.rbxes()
    boxes = sorted(list(set([rbx[-2:] for rbx in rbxList])))
    dets  = sorted(list(set([rbx[:-2] for rbx in rbxList])))

    nSpaces = 5
    header = " ".join(["RBX".ljust(nSpaces)] + boxes)
    print header
    print "-" * len(header)
    for det in dets:
        row = []
        for box in boxes:
            key = det + box
            nFibers = rbxes.get(key)
            if nFibers is None:
                row.append(zero)
            else:
                row.append("%2d" % nFibers)
        print " ".join([det.ljust(nSpaces)] + row)
    print


def report(extra=None, missing=None, different=None, same=None, nMissingMax=None):
    assert nMissingMax is not None

    printTable(fiberCount(same.values()), header="Fibers matching reference")
    nMissing = fiberCount(missing.values())
    printTable(nMissing, header="Fibers in reference, but either not acquired or having 8b/10b errors")

    header = "| RBXes with (1 <= n missing fibers <= %d) |" % nMissingMax
    print "-" * len(header)
    print header
    print "-" * len(header)
    print "DCC(CR) SP(HTR) FI: ref. RBX RM FI"

    count = 0
    for iMissing in range(1, 1 + nMissingMax):
        count += nMissing.values().count(iMissing)
    if not count:
        print "None"

    for be, ref in sorted(missing.iteritems()):
        rbx = ref[0]
        if 1 <= nMissing[rbx] <= nMissingMax:
            print pretty(be=be, fe=ref)

    print
    print "-----------------------------------"
    print "| Fibers differing from reference |"
    print "-----------------------------------"
    if different:
        print "DCC(CR) SP(HTR) FI: ref. RBX RM FI  |   cabled"
        for be, (ref, cabled) in sorted(different.iteritems()):
            print pretty(be=be, fe=ref) + "  | " + pretty(fe=cabled)
    else:
        print "None"

    print
    print "--------------------------------------------------------"
    print "| Fibers acquired and valid, but absent from reference |"
    print "--------------------------------------------------------"
    if extra:
        print "DCC(CR) SP(HTR) FI: cabled"
        for be, fe in sorted(extra.iteritems()):
            print pretty(be=be, fe=fe)
    else:
        print "None"


def go(fileName="", nMissingMax=None):
    assert fileName
    with open(fileName) as f:
        ref, refMisc = mapping(f)
    assert not refMisc, "refMisc='%s'" % refMisc

    cabled, misc = mapping(sys.stdin, skip=["Xrd", "TClassTable", "nologin"])
    print "".join(misc)

    report(*diffs(ref, cabled), nMissingMax=nMissingMax)


def opts():
    parser = optparse.OptionParser(usage="usage: %prog [options] reference_file.txt")
    parser.add_option("--nMissingMax",
                      dest="nMissingMax",
                      default="2",
                      metavar="n",
                      help="maximum number of missing fibers per RBX to print in detailed table (default is 2)")

    options, args = parser.parse_args()
    if not args:
        parser.print_help()
        sys.exit(1)
    return options, args[0]


if __name__ == "__main__":
    options, ref = opts()
    go(ref, int(options.nMissingMax))
