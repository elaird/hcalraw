#!/usr/bin/env python

import configuration
import fileinput


def mapping(file=None, skip=[]):
    out = {}
    misc = []
    for line in file:
        if any([item in line for item in skip]):
            continue

        if ":" in line:
            be, fe = line.split(":")
            out[tuple(be.split())] = tuple(fe.split())
        elif line != "\n":
            misc.append(line)
    return out, misc


def diffs(ref={}, cabled={}):
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
    return missing, different, same


def pretty(be=None, fe=None):
    if be:
        dcc, sp, fi = be
        exp = configuration.expectedHtr(int(dcc), int(sp))
        htr = "%2d%1s" % (exp["Slot"], exp["Top"])
        s = "%3s %2s(%3s) %2s:  " % (dcc, sp, htr, fi)
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

    boxes = ["%02d" % i for i in range(1, 19)]
    dets = ["HBM", "HBP",
            "HEM", "HEP",
            "HFM", "HFP",
            "HO2M", "HO1M", "HO0", "HO1P", "HO2P"]
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


def report(missing=None, different=None, same=None):
    printTable(fiberCount(same.values()), header="Fibers matching reference")
    nMissing = fiberCount(missing.values())
    printTable(nMissing, header="Missing Fibers")

    header = "| RBXes missing exactly one fiber |"
    print "-"*len(header)
    print header
    print "-"*len(header)
    print "DCC SP(HTR) FI: ref. RBX RM FI"
    if not nMissing.values().count(1):
        print "None"

    for be, ref in sorted(missing.iteritems()):
        rbx = ref[0]
        if nMissing[rbx] == 1:
            print pretty(be=be, fe=ref)

    print
    print "---------------"
    print "| Differences |"
    print "---------------"
    if different:
        print "DCC SP(HTR) FI: ref. RBX RM FI  |   cabled"
        for be, (ref, cabled) in sorted(different.iteritems()):
            print pretty(be=be, fe=ref) + "  | " + pretty(fe=cabled)
    else:
        print "None"


if __name__ == "__main__":
    with open("data/ref.txt") as f:
        ref, refMisc = mapping(f)

    cabled, misc = mapping(fileinput.input(), skip=["Xrd", "TClassTable", "nologin"])

    assert not refMisc
    for item in sorted(misc):
        print item

    report(*diffs(ref, cabled))
