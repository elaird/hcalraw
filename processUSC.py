#!/usr/bin/env python

import os
import subprocess
import sys


def commandOutput(command):
    p = subprocess.Popen(command,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return {"command": command,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": p.returncode}


def stdout(cmd="", checkErr=True):
    out = commandOutput(cmd)
    if checkErr:
        assert not out["stderr"], "%s \n\n %s" % (cmd, out["stderr"])
    return out["stdout"].split("\n")


def prepareRunList(dest="", hcalRuns=""):
    dirName = os.path.dirname(dest)
    if not os.path.exists(dirName):
        print "Creating %s" % dirName
        os.makedirs(dirName)

    if os.path.exists(dest):
        try:
            os.remove(dest)
        except OSError, e:
            assert e.no == 2

    stdout("wget -O %s %s" % (dest, hcalRuns), checkErr=False)


def rootFiles(eosDir=""):
    cmd = "\n".join(["source /afs/cern.ch/project/eos/installation/cms/etc/setup.sh",
                     "eos ls %s | grep 'USC_[0-9]\{6\}\.root'" % eosDir,
                     ])
    return stdout(cmd)


def prepareDir(baseDir="", run=0, suffix=""):
    thisDir = "%s/%d" % (baseDir, run)
    if not os.path.exists(thisDir):
        os.mkdir(thisDir)

    procFlag = "%s/processing.%s" % (thisDir, suffix)
    doneFlag = "%s/.processed.%s" % (thisDir, suffix)

    if os.path.exists(procFlag):
        print "Run %d (%s) is being processed already." % (run, suffix)
        return [""]*3
    elif os.path.exists(doneFlag):
        return [""]*3
    else:
        return thisDir, procFlag, doneFlag


def selectedRuns(select=lambda x: False, runListFile=""):
    f = open(runListFile)
    out = []
    for line in f:
        fields = line.split()
        if len(fields) != 4:
            continue
        if select(fields[3]):
            try:
                run = int(fields[0])
                out.append(run)
            except ValueError:
                continue
    f.close()
    return out


def goodRun(rootFile=""):
    if not rootFile:
        return
    try:
        return int(rootFile[-11:-5])
    except ValueError:
        print "Could not determine run number from file named '%s'." % rootFile
        return


def oneRun(args=[], outputFile=""):
    out = " && ".join(["cd ~elaird/public/hcalraw_pro",
                       "source env/slc6-cmssw.sh",
                       "./oneRun.py "
                       ])
    out += " ".join(args)
    out += " >& %s" % outputFile
    return out


def processFiberId(inputFile="", outputDir="", run=0):
    outputFile = "%s/cabled.txt" % outputDir
    args = ["--file1='%s'" % inputFile,
            "--feds1=HCAL",
            "--patterns",
            "--nevents=1",
            ]
    cmd = oneRun(args, outputFile)

    diffFile = "%s/summary.txt" % outputDir
    cmd += " && cat %s | ./diff.py > %s" % (outputFile, diffFile)
    return commandOutput(cmd)


def utcaArgs(inputFile=""):
    return ["--file1='%s' --feds1=929 --feds2=721,722" % inputFile]


def dumpOneEvent(inputFile="", outputDir="", run=0):
    args = utcaArgs(inputFile) + ["--nevents=1 --dump=4"]
    cmd = oneRun(args, outputFile="%s/1event.txt" % outputDir)
    return commandOutput(cmd)


def compare(inputFile="", outputDir="", run=0):
    args = utcaArgs(inputFile) + ["--nevents=1000 --identity-map --no-color"]
    cmd = oneRun(args, outputFile="%s/comparison.txt" % outputDir)
    return commandOutput(cmd)


def report(d={}, subject=""):
    print subject
    lines = []
    for key, value in sorted(d.iteritems()):
        lines += ["* %s *" % key, "",
                  str(value).replace("&&", "&&\n"),
                  "", ""]

    if d.get("stderr") or d.get("returncode"):
        cmd = "echo '%s' |& mail -s '%s' %s" % ("\n".join(lines),
                                                subject,
                                                os.environ["USER"])
        os.system(cmd)


def go(baseDir="",
       runListFile="",
       select=lambda x: False, 
       process=lambda inputFile, outputDir, run: {},
       minimumRun=None,
       maximumRun=None,
       eosPrefix="root://eoscms.cern.ch",
       eosDir="/eos/cms/store/group/comm_hcal/LS1",
       jobCheck="oneRun",
       nProcMax=5,
       ):
    assert runListFile
    runs = filter(lambda x: minimumRun <= x, selectedRuns(select, runListFile))
    if maximumRun:
        runs = filter(lambda x: x <= maximumRun, runs)

    for rootFile in rootFiles(eosDir):
        run = goodRun(rootFile)
        if run not in runs:
            continue

        processes = stdout("ps -ef | grep %s | grep %s" % (os.environ["USER"], jobCheck))
        if nProcMax < len(processes):
            msg = "Already %d processes:" % len(processes)
            msg += "\n".join(processes)
            sys.exit(msg)

        suffix = process.__name__
        runDir, procFlag, doneFlag = prepareDir(baseDir, run, suffix=suffix)
        if runDir:
            stdout("touch %s" % procFlag)
            d = process(inputFile="%s/%s/%s" % (eosPrefix, eosDir, rootFile),
                        outputDir=runDir,
                        run=run)
            report(d, subject='Run %d: %s' % (run, suffix))
            stdout("rm %s" % procFlag)
            stdout("touch %s" % doneFlag)


if __name__ == "__main__":
    runListFile = "%s/public/html/runlist.txt" % os.environ["HOME"]
    prepareRunList(dest=runListFile,
                   hcalRuns="http://cmshcalweb01.cern.ch/HCALruns.txt",
                   )

    go(baseDir="%s/public/FiberID" % os.environ["HOME"],
       runListFile=runListFile,
       select=lambda x: "FiberID" in x,
       process=processFiberId,
       minimumRun=214782,
       #minimumRun=217920,
       #maximumRun=217940,
       )

    for func in [dumpOneEvent, compare]:
        go(baseDir="%s/public/uTCA" % os.environ["HOME"],
           runListFile=runListFile,
           select=lambda x: ("/HF/" in x) and ("no_utca" not in x),
           process=func,
           minimumRun=219866,
           )
