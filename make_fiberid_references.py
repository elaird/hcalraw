#!/usr/bin/env python

import collections, sys
from configuration.patterns import lineStart


def B904():
    # RM
    crate = 61
    slot = 1
    uhtr_fib = -1
    for iRbx in range(1, 14):
        rbx = "HB%02d" % iRbx
        for rm in range(1, 5):
            for rm_fib in range(1, 9):
                uhtr_fib += 1
                if 23 < uhtr_fib:
                    uhtr_fib -= 24
                    slot += 1
                if 12 < slot:
                    slot -= 12
                    crate += 1
                print("%su%2d %02d %02d: %s %1d %1d" % (lineStart, crate, slot, uhtr_fib, rbx, rm, rm_fib))

    # CU
    crate = 63
    slot = 9
    uhtr_fib = -1
    for iRbx in range(1, 14):
        rbx = "HB%02d" % iRbx
        rm = 5
        for rm_fib in [1, 2]:
            uhtr_fib += 1
            if 23 < uhtr_fib:
                uhtr_fib -= 12
                slot -= 1
            print("%su%2d %02d %02d: %s %1d %1d" % (lineStart, crate, slot, uhtr_fib, rbx, rm, rm_fib))


def loop(filenames=[], nExpected=None, iCrate=None, iUhtr=None, iUhtrFib=None, iRbx=None, iRm=None, iRmFib=None):
    out = []
    for filename in filenames:
        f = open(filename)
        for line in f:
            if line.startswith("#") or not line:
                continue
            fields = line.split()
            if not fields:
                continue

            if fields[0][1:] == "ide" or fields[0].startswith("#"):
                continue

            if len(fields) != nExpected and nExpected is not None:
                print(len(fields), fields)
                continue

            be = "u%2d %02d %02d" % (int(fields[iCrate]), int(fields[iUhtr]), int(fields[iUhtrFib]))
            fe = "%s %1d %1d" % (fields[iRbx], int(fields[iRm]), int(fields[iRmFib]))
            out.append("%s%s: %s" % (lineStart, be, fe))
        f.close()
    return out


def check_for_duplicates(l):
    fes = collections.defaultdict(list)
    for x in sorted(l):
        be, fe = x.replace(lineStart, "").split(":")
        fes[be].append(fe)

    for be, lst in sorted(fes.items()):
        if len(lst) != 1:
            sys.exit("found duplicates: %s %s" % (be, str(lst)))


def HB():
    return loop(["Lmap_ngHB_N_20191210.txt"], nExpected=27,
                iCrate=-7, iUhtr=-6, iUhtrFib=-5, iRbx=6, iRm=12, iRmFib=13)


def HBcalib():
    return loop(["Lmap_ngHBcalib_N_20191210.txt"], nExpected=31,
                iCrate=-5, iUhtr=-4, iUhtrFib=-3, iRbx=6, iRm=11, iRmFib=12)


def HE():
    return loop(["Lmap_ngHE_N_20191210.txt"], nExpected=27,
                iCrate=-7, iUhtr=-6, iUhtrFib=-5, iRbx=6, iRm=12, iRmFib=13)


def HEcalib():
    return loop(["Lmap_ngHEcalib_N_20191210.txt"], nExpected=31,
                iCrate=26, iUhtr=27, iUhtrFib=28, iRbx=6, iRm=11, iRmFib=12)


def HF():
    return loop(["Lmap_ngHF_N_20191210.txt"], nExpected=36,
                iCrate=27, iUhtr=28, iUhtrFib=30, iRbx=6, iRm=19, iRmFib=22)


def HFcalib():
    return loop(["Lmap_ngHFcalib_N_20191210.txt"], nExpected=23,
                iCrate=-6, iUhtr=-5, iUhtrFib=-4, iRbx=6, iRm=8, iRmFib=10)


def HO():
    return loop(["Lmap_ngHO_N_20191210.txt"], nExpected=22,  # deleting the final four columns from most rows
                iCrate=16, iUhtr=17, iUhtrFib=19, iRbx=6, iRm=12, iRmFib=13)


def HOcalib():
    return loop(["Lmap_ngHOcalib_N_20191210.txt"], nExpected=22,
                iCrate=16, iUhtr=17, iUhtrFib=19, iRbx=6, iRm=12, iRmFib=13)


def USC():
    # see https://hypernews.cern.ch/HyperNews/CMS/get/hcal-performance/1609.html
    # and http://cmsdoc.cern.ch/cms/HCALdocs/document/Mapping/Yuan/2019-dec-10/Lmap/
    l = HB() + HBcalib() + HE() + HEcalib() + HF() + HFcalib() + HO() + HOcalib()
    l = set(l)
    check_for_duplicates(l)
    for line in sorted(l):
        print(line)


if __name__ == "__main__":
    # B904()
    USC()
