#!/usr/bin/env python

import os,optparse

def opts() :
    parser = optparse.OptionParser()
    parser.add_option("--min", dest = "min", default = None, metavar = "N", help = "specify minimum run number")
    parser.add_option("--max", dest = "max", default = None, metavar = "N", help = "specify maximum run number")
    parser.add_option("--run", dest = "run", default = None, metavar = "N", help = "specify one run number")
    parser.add_option("--only-utca", dest = "onlyutca", default = False, action = "store_true", help = "ignore uTCA file if present")
    parser.add_option("--only-cms",  dest = "onlycms",  default = False, action = "store_true", help = "ignore CMS file if present")

    options,args = parser.parse_args()
    return options

def rootFiles(directory = "", mode = "") :
    assert mode in ["usc","castor"],mode
    directory2 = directory+"/"+mode
    d = {}
    for item in sorted(os.listdir(directory2)) :
        if mode=="usc" :
            fields = item.split("_")
            if len(fields)<3 : continue
            if fields[0]!="USC" or fields[1]!="uTCA" : continue
            run,root = fields[2].split(".")
            if root!="root" : continue

        if mode=="castor":
            fields = item.split(".")
            if len(fields)<3 : continue
            if fields[1]=="A" : continue
            run = fields[0]

        d[int(run)] = "%s/%s"%(directory2, item)
    return d

directory = "/afs/cern.ch/user/e/elaird/work/public/d1_utca/"
uscFiles    = rootFiles(directory, mode = "usc")
castorFiles = rootFiles(directory, mode = "castor")

options = opts()
import analyze

for run in sorted(uscFiles.keys()) :
    if any([options.min and run<int(options.min),
            options.max and run>int(options.max),
            options.run and run!=int(options.run),
            (not options.onlyutca) and (run not in castorFiles),
            ]) : continue

    analyze.oneRun(utcaFileName = "" if options.onlycms  else uscFiles[run],
                   cmsFileName  = "" if options.onlyutca else castorFiles[run],
                   label = "Run%d"%run, useEvN = False)
