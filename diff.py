#!/usr/bin/env python

from configuration import patterns as conf
import configuration.hw
import argparse, sys


def rbx_list(reference):
    dets = []
    boxes = []
    for rbx, rm, fi in reference.values():
        dets.append(rbx[:-2])
        boxes.append(rbx[-2:])

    return sorted(set(dets)), sorted(set(boxes))


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
    for be, fe in sorted(ref.items()):
        if be not in cabled:
            missing[be] = fe
            continue

        if fe != cabled[be]:
            different[be] = (fe, cabled[be])
        else:
            same[be] = fe

    for be, fe in cabled.items():
        if be not in ref:
            extra[be] = fe

    return extra, missing, different, same


def pretty(be=None, fe=None, vme=False):
    if be:
        dcc, sp, fi = be
        if dcc.startswith("u"):
            crate = dcc[1:]
            slot = sp
            if vme:
                s = "    %2s     %2s   %2s:  " % (crate, slot, fi)
            else:
                s = "%2s %2s %2s:  " % (crate, slot, fi)
        else:
            crate = conf.expectedCrate(int(dcc))
            exp = configuration.hw.expectedVmeHtr(int(dcc), int(sp))
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


def printTable(rbxes={}, header="", zero="  ", reference=None, onlyDet=None, excludeDet=None):
    if header:
        header = "| %s |" % header
        print("")
        print("-"*len(header))
        print(header)
        print("-"*len(header))

    dets, boxes = rbx_list(reference)

    nSpaces = 5
    header = " ".join(["RBX".ljust(nSpaces)] + boxes)
    print(header)
    print("-" * len(header))
    for det in dets:
        if onlyDet and (onlyDet not in det):
            continue
        if excludeDet and (excludeDet in det):
            continue
        row = []
        for box in boxes:
            key = det + box
            nFibers = rbxes.get(key)
            if nFibers is None:
                row.append(zero)
            else:
                row.append("%2d" % nFibers)
        print(" ".join([det.ljust(nSpaces)] + row))
    print


def report(extra=None, missing=None, different=None, same=None, reference=None, options=None):
    nMissingMin = options.nMissingMin
    nMissingMax = options.nMissingMax

    printTable(fiberCount(same.values()),
               header="Fibers matching reference",
               reference=reference,
               onlyDet=options.only,
               excludeDet=options.exclude)
    nMissing = fiberCount(missing.values())
    printTable(nMissing,
               header="Fibers in reference, but either not acquired or having FE link errors",
               reference=reference,
               onlyDet=options.only,
               excludeDet=options.exclude)

    header = "| RBXes with (%d <= n missing fibers <= %d) |" % (nMissingMin, nMissingMax)
    print("")
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    if options.vme:
        print("DCC(CR) SP(HTR) FI: ref. RBX RM FI")
    else:
        print("CR SL FI: ref. RBX RM FI")

    count = 0
    for iMissing in range(nMissingMin, 1 + nMissingMax):
        count += list(nMissing.values()).count(iMissing)
    if not count:
        print("None")

    for be, ref in sorted(missing.items()):
        rbx = ref[0]
        if nMissingMin <= nMissing[rbx] <= nMissingMax:
            print(pretty(be=be, fe=ref, vme=options.vme))

    print("")
    print("-----------------------------------")
    print("| Fibers differing from reference |")
    print("-----------------------------------")
    if different:
        if options.vme:
            print("DCC(CR) SP(HTR) FI: ref. RBX RM FI  |   cabled")
        else:
            print("CR SL FI: ref. RBX RM FI  |   cabled")
        for be, (ref, cabled) in sorted(different.items()):
            print(pretty(be=be, fe=ref, vme=options.vme) + "  | " + pretty(fe=cabled, vme=options.vme))
    else:
        print("None")

    print("")
    print("--------------------------------------------------------")
    print("| Fibers acquired and valid, but absent from reference |")
    print("--------------------------------------------------------")
    if extra:
        if options.vme:
            print("DCC(CR) SP(HTR) FI: cabled")
        else:
            print("CR SL FI: cabled")
        for be, fe in sorted(extra.items()):
            print(pretty(be=be, fe=fe, vme=options.vme))
    else:
        print("None")


def go(options):
    with open(options.reference_file) as f:
        ref, refMisc = mapping(f)
    assert not refMisc, "refMisc='%s'" % refMisc

    cabled, misc = mapping(sys.stdin, skip=["Xrd", "TClassTable", "nologin"])
    if misc:
        print("".join(misc))

    report(*diffs(ref, cabled), reference=ref, options=options)


def opts():
    parser = argparse.ArgumentParser()

    parser.add_argument("reference_file",
                        metavar="FILE",
                        help="reference file to compare against")
    parser.add_argument("--n-missing-min",
                        dest="nMissingMin",
                        default=1,
                        metavar="n",
                        type=int,
                        help="maximum number of missing fibers per RBX to print in detailed table (default is %(default)s)")
    parser.add_argument("--n-missing-max",
                        dest="nMissingMax",
                        default=2,
                        metavar="n",
                        type=int,
                        help="maximum number of missing fibers per RBX to print in detailed table (default is %(default)s)")
    parser.add_argument("--vme",
                        default=False,
                        action="store_true",
                        help="support VME (DCC/spigot)")
    parser.add_argument("--only",
                        help="suppress row in table if this string is absent from RBX name")
    parser.add_argument("--exclude",
                        help="suppress row in table if this string is present in RBX name")

    return parser.parse_args()


if __name__ == "__main__":
    go(opts())
