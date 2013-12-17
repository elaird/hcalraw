#!/usr/bin/env python

import optparse
import os


def opts():
    parser = optparse.OptionParser("usage: %prog dump.out")
    parser.add_option("--prune", dest="prune", default="", help="comma-separated list of items to 'grep -v' from reference file")
    options, args = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        exit()
    return args[0], options.prune.split(",")


def printList(l=[], s=""):
    for item in sorted(l):
        print s, item


def not_installed():
    return ["HO002",
            "HO003",
            "HO006",
            "HO010",
            "HO011",
            "HO1P02",
            "HO1P06",
            "HO1P08",
            "HO1P10",
            "HO1P12",
            "HO2P02",
            "HO2P06",
            "HO2P08",
            "HO2P10",
            "HO2P12",
            ]


def prepare(refBig="", ref="", ignore=[]):
    cmd = "cat %s %s > %s" % (refBig, " | grep -v ".join([""]+ignore), ref)
    os.system(cmd)


def diff(ref="", cabled=""):
    cmd = "diff -By --suppress-common-lines %s %s" % (ref, cabled)
    os.system(cmd)

cabled, prune = opts()
ignore = not_installed() + prune

printList(ignore, "(ignored)")
ref = "ref_pruned.txt"
prepare(refBig="data/ref.txt", ref=ref, ignore=ignore)
diff(ref=ref, cabled=cabled)
