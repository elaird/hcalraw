#!/usr/bin/env python

import os,optparse,subprocess,cProfile

def opts() :
    parser = optparse.OptionParser()
    parser.add_option("--profile", dest = "profile", default = False, action = "store_true", help = "profile the run")
    parser.add_option("--min", dest = "min", default = None, metavar = "N", help = "specify minimum run number")
    parser.add_option("--max", dest = "max", default = None, metavar = "N", help = "specify maximum run number")
    parser.add_option("--run", dest = "run", default = None, metavar = "N", help = "specify one run number")
    parser.add_option("--only-utca", dest = "onlyutca", default = False, action = "store_true", help = "ignore uTCA file if present")
    parser.add_option("--only-cms",  dest = "onlycms",  default = False, action = "store_true", help = "ignore CMS file if present")
    parser.add_option("--filter-evn",dest = "filterevn",default = False, action = "store_true", help = "consider only events with EvN&0x1fff == 0")
    parser.add_option("--only-summary",dest = "onlysummary",default = False, action = "store_true", help = "do not loop; simply make summary plots from existing ROOT files")

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
            run = fields[0]

        d[int(run)] = "%s/%s"%(directory2, item)
    return d

def commandOutput(cmd = "") :
    return subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE).communicate()[0].split()

def eosFile(run) :
    #eos not available; list with castor
    castor = "/castor/cern.ch/cms"
    eos = "root://eoscms.cern.ch//eos/cms"
    dir = "%s/store/hidata/HIRun2013/HcalNZS/RAW/v1/000/%03d/%03d/00000/"%(castor, run/1000, run%1000)
    fileList = commandOutput(cmd = "nsls %s"%dir)
    if fileList :
        return dir.replace(castor, eos)+fileList[0]
    else:
        return ""

options = opts()
import analyze,graphs

def go() :
    directory = "/afs/cern.ch/user/e/elaird/work/public/d1_utca/"
    uscFiles    = rootFiles(directory, mode = "usc")
    castorFiles = rootFiles(directory, mode = "castor")

    labels = []
    for run in sorted(uscFiles.keys()) :
        if any([options.min and run<int(options.min),
                options.max and run>int(options.max),
                options.run and run!=int(options.run),
                #(not options.onlyutca) and (run not in castorFiles),
                ]) : continue
        label = "Run%d"%run
        labels.append(label)
        if options.onlysummary : continue

        analyze.oneRun(utcaFileName = "" if options.onlycms  else uscFiles[run],
                       #cmsFileName  = "" if options.onlyutca else castorFiles[run],
                       cmsFileName  = "" if options.onlyutca else eosFile(run),
                       label = label, useEvn = False,
                       filterEvn = options.filterevn, ornTolerance = 1)

    graphs.makeSummaryPdf(labels)

if __name__=="__main__" :
    if options.profile :
        cProfile.run("go()", sort = "time")
    else :
        go()
