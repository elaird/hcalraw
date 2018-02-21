#!/usr/bin/env python2

from configuration.patterns import lineStart


def B904():
    crate = 61
    slot = 1
    uhtr_fib = -1

    for iRbx in range(1, 19):
        rbx = "HE%d" % iRbx
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


def loop(filenames=[], nExpected=None, iCrate=None, iUhtr=None, iUhtrFib=None, iRbx=None, iRm=None, iRmFib=None, vme=False):
    out = []
    for filename in filenames:
        f = open(filename)
        for line in f:
            if line.startswith("#") or not line:
                continue
            fields = line.split()
            if len(fields) != nExpected and nExpected is not None:
                print len(fields), fields
                continue

            if vme:
                be = "%3s %02d %02d" % (int(fields[iCrate]), int(fields[iUhtr]), int(fields[iUhtrFib]))  # fedId spigot fiber
            else:
                be = "u%2d %02d %02d" % (int(fields[iCrate]), int(fields[iUhtr]), int(fields[iUhtrFib]))

            fe = "%s %1d %1d" % (fields[iRbx], int(fields[iRm]), int(fields[iRmFib]))
            if "HF" in filename:
                fe = "%s %1d %1d" % (fields[iRbx], int(fields[iRm]), int(fields[iRmFib]) - 4)
            out.append("%s%s: %s" % (lineStart, be, fe))
        f.close()
    return out


def HBHE():
    return loop(["2018HCALLMap_HB_K_20180131.txt", "2018HCALLMap_ngHE_K_20180214.txt"], nExpected=26,
                iCrate=19, iUhtr=20, iUhtrFib=21, iRbx=6, iRm=11, iRmFib=12)


def HBHEcalib():
    return loop(["2018HCALLMap_HBCalib_K_20180214.txt", "2018HCALLMap_ngHECalib_K_20180216.txt"], nExpected=29,
                iCrate=24, iUhtr=25, iUhtrFib=26, iRbx=6, iRm=10, iRmFib=11)


def HF():
    return loop(["2018HCALLMap_ngHF_K_20180131.txt"], nExpected=37,
                iCrate=27, iUhtr=28, iUhtrFib=30, iRbx=6, iRm=19, iRmFib=22)


def HFcalib():
    return loop(["2018HCALLMap_ngHFCalib_K_20180201.txt"], nExpected=18,
                iCrate=13, iUhtr=14, iUhtrFib=15, iRbx=6, iRm=8, iRmFib=10)


def HO():
    return loop(["2018HCALLMap_HO_K_20180131.txt"], nExpected=25, vme=True,
                iCrate=-2, iUhtr=-4, iUhtrFib=19, iRbx=6, iRm=12, iRmFib=13)


def HOcalib():
    return loop(["HO_CU_Lmap_2018_K.txt"], vme=True, # nExpected=40,
                iCrate=-15, iUhtr=-7, iUhtrFib=-6, iRbx=7, iRm=11, iRmFib=12)  # use negatives to avoid ragged pp assignment


def USC():
    l = HBHE() + HBHEcalib() + HF() + HFcalib() + HO() + HOcalib()
    for line in sorted(set(l)):
        print(line)


if __name__ == "__main__":
    # B904()
    USC()
