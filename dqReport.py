#!/usr/bin/env python

import sys
import multi
import ROOT as r

def main(runs=[]):
    for run in runs:
        f = r.TFile("output/%d.root" % run)
        f.Close()


if __name__ == "__main__":
    main(multi.runs(sys.stdin))
