#!/usr/bin/env python

import os
import subprocess


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


def prepareDir(baseDir="", run=0):
    thisDir = "%s/%d" % (baseDir, run)
    if not os.path.exists(thisDir):
        os.mkdir(thisDir)

    procFlag = "%s/processing" % thisDir
    doneFlag = "%s/.processed" % thisDir

    if os.path.exists(procFlag):
        print "Run %d is being processed already." % run
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


def processFiberId(inputFile="", outputDir="", run=0):
    cmd = " && ".join(["cd ~elaird/public/hcalraw_pro",
                       "source env/slc6-cmssw.sh",
                       "./oneRun.py "
                       ])

    outputFile = "%s/cabled.txt" % outputDir
    cmd += " ".join(["--file1='%s'" % inputFile,
                     "--feds1=HCAL",
                     "--patterns",
                     "--nevents=1",
                     ">& %s" % outputFile,
                     ])
    diffFile = "%s/summary.txt" % outputDir
    cmd += " && cat %s | ./diff.py > %s" % (outputFile, diffFile)
    return commandOutput(cmd)


def process_utca(inputFile="", outputDir="", run=0):
    cmd = " && ".join(["cd ~elaird/hcalraw",
                       "source env/slc6-cmssw.sh",
                       "./oneRun.py "
                       ])

    cmd += " ".join(["--file1='%s'" % inputFile,
                     "--feds1=929",
                     "--feds2=721,722",
                     "--nevents=1",
                     "--dump=4",
                     ">& %s/1event.txt" % outputDir,
                     ])
    return commandOutput(cmd)


def report(d={}, subject=""):
    print subject
    lines = []
    for key, value in sorted(d.iteritems()):
        lines += ["* %s *" % key, "",
                  str(value).replace("&&", "&&\n"),
                  "", ""]

    if d.get("stderr"):  # or d.get("returncode"):
        cmd = "echo '%s' |& mail -s '%s' %s" % ("\n".join(lines),
                                                subject,
                                                os.environ["USER"])
        os.system(cmd)


def go(baseDir="",
       select=lambda x: False, 
       process=lambda inputFile, outputDir, run: {},
       minimumRun=None,
       maximumRun=None,
       hcalRuns="http://cmshcalweb01.cern.ch/HCALruns.txt",
       eosPrefix="root://eoscms.cern.ch",
       eosDir="/eos/cms/store/group/comm_hcal/LS1",
       jobCheck="oneRun",
       nProcMax=5,
       ):

    runListFile = "%s/runlist.txt" % baseDir
    prepareRunList(dest=runListFile, hcalRuns=hcalRuns)
    runs = filter(lambda x: minimumRun <= x, selectedRuns(select, runListFile))
    if maximumRun:
        runs = filter(lambda x: x <= maximumRun, runs)

    for rootFile in rootFiles(eosDir):
        run = goodRun(rootFile)
        if run not in runs:
            continue

        processes = stdout("ps -ef | grep %s | grep %s" % (os.environ["USER"], jobCheck))
        if nProcMax < len(processes):
            print "Already %d processes:" % len(processes)
            print "\n".join(processes)
            exit()

        runDir, procFlag, doneFlag = prepareDir(baseDir, run)
        if runDir:
            stdout("touch %s" % procFlag)
            d = process(inputFile="%s/%s/%s" % (eosPrefix, eosDir, rootFile),
                        outputDir=runDir,
                        run=run)
            report(d, subject='Run %d' % run)
            stdout("rm %s" % procFlag)
            stdout("touch %s" % doneFlag)


if __name__ == "__main__":
    go(baseDir="%s/public/FiberID" % os.environ["HOME"],
       select=lambda x: "FiberID" in x,
       process=processFiberId,
       minimumRun=214782,
       #minimumRun=217920,
       #maximumRun=217940,
       )

    go(baseDir="%s/public/uTCA" % os.environ["HOME"],
       select=lambda x: ("/HF/" in x) and ("no_utca" not in x),
       process=process_utca,
       minimumRun=219866,
       )

