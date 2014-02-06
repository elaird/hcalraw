#!/usr/bin/env python

import fileinput


def mapping(file=None):
    out = {}
    misc = []
    for line in file:
        if ":" in line:
            be, fe = line.split(":")
            out[tuple(be.split())] = tuple(fe.split())
        elif line != "\n":
            misc.append(line)
    return out, misc


def diffs(ref={}, cabled={}):
    missing = {}
    different = {}
    for be, fe in sorted(ref.iteritems()):
        if be not in cabled:
            missing[be] = fe
            continue

        if fe != cabled[be]:
            different[be] = (fe, cabled[be])

    return missing, different


def pretty(be, ref):
    s = "%3s %2s %2s:  " % be
    s += " %6s %2s %2s" % ref
    return s


def report(missing=None, different=None):
    print "---------------"
    print "| Differences |"
    print "---------------"
    if different:
        print "DCC SP FI: ref. RBX RM FI  |  cabled"
        for be, (ref, cabled) in sorted(different.iteritems()):
            print pretty(be, ref) + "  |  " + " ".join(cabled)
    else:
        print "None"

    if missing:
        rbxes = [x[0] for x in missing.values()]
        header = "| RBXes missing exactly one fiber |"
        print
        print "-"*len(header)
        print header
        print "-"*len(header)
        print "DCC SP FI: ref. RBX RM FI"

        nSingle = 0
        for be, ref in sorted(missing.iteritems()):
            rbx = ref[0]
            if rbxes.count(rbx) == 1:
                print pretty(be, ref)
                rbxes.remove(rbx)
                nSingle += 1
        if not nSingle:
            print "None"

        header = "| RBXes missing at least two fibers |"
        print
        print "-"*len(header)
        print header
        print "-"*len(header)
        if rbxes:
            for rbx in sorted(set(rbxes)):
                print "%6s (%2d fibers)" % (rbx, rbxes.count(rbx))
        else:
            print "None"


if __name__ == "__main__":
    with open("data/ref.txt") as f:
        ref, refMisc = mapping(f)

    cabled, misc = mapping(fileinput.input())

    assert not refMisc
    for item in sorted(misc):
        print item

    report(*diffs(ref, cabled))
