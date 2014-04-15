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


def blob(d={}, newlines=["&&", "|&", ">&"]):
    def s(x):
        o = str(x)
        for item in newlines:
            o = o.replace(item, "%s\n" % item)
        return o

    lines = []
    for key, value in sorted(d.iteritems()):
        lines += ["* %s *" % key, "", s(value), "", ""]

    return "\n".join(lines)


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


def makeDir(baseDir="", run=0):
    out = "%s/%d" % (baseDir, run)
    if not os.path.exists(out):
        os.mkdir(out)
    return out


def flags(runDir="", run=0, suffix="", dependsUpon=[]):
    def proc(s):
        return "%s/processing.%s" % (runDir, s)
    def done(s):
        return "%s/.processed.%s" % (runDir, s)

    yes = (True, proc(suffix), done(suffix))
    no = (False, "", "")

    notReady = filter(lambda x: not os.path.exists(done(x)), dependsUpon)

    if os.path.exists(proc(suffix)):
        print "Run %d (%s) is being processed already." % (run, suffix)
        return no
    elif notReady:
        print "These dependencies are not ready:", notReady
        return no
    elif os.path.exists(done(suffix)):
        return no
    else:
        return yes


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


def env():
    return ["cd ~elaird/public/hcalraw_pro", "source env/slc6-cmssw.sh"]


def gitLog(inputFile="", outputDir="", run=0):
    cmds = ["git log | grep %s | head -1" % s for s in ["commit", "Date"]]
    return commandOutput(" && ".join(env() + cmds))


def oneRun(args=[], outputFile="", suppress=["Xrd", "nologin"]):
    out = " && ".join(env() + ["./oneRun.py "])
    out += " ".join(args)
    for item in suppress:
        out += " |& grep -v %s" % item
    out += " >& %s" % outputFile
    return out


def dumpFibering(inputFile="", outputDir="", run=0):
    outputFile = "%s/cabled.txt" % outputDir
    args = ["--file1='%s'" % inputFile,
            "--feds1=HCAL",
            "--patterns",
            "--nevents=1",
            ]
    return commandOutput(oneRun(args, outputFile))


def compareFibering(inputFile="", outputDir="", run=0):
    cmd = "cat %s/cabled.txt | ./diff.py > %s/summary.txt" % (outputDir,
                                                              outputDir)
    return commandOutput(" && ".join(env() + [cmd]))


def utcaArgs(inputFile=""):
    return ["--file1='%s'" % inputFile,
            "--feds1=929 --feds2=721,722",
            "--identity-map --no-warn-skip16"]


def dumpEventsNoColor(**kargs):
    kargs["color"] = False
    return dumpEvents(**kargs)


def dumpEvents(inputFile="", outputDir="", run=0, n=3, color=True):
    args = utcaArgs(inputFile) + ["--dump=4 --nevents=%d" % n]
    outputFile = "%s/%devents.txt" % (outputDir, n)
    if color:
        outputFile = outputFile.replace(".txt", "_color.txt")
    else:
        args.append("--no-color")
    cmd = oneRun(args, outputFile=outputFile)
    return commandOutput(cmd)


def compare(inputFile="", outputDir="", run=0):
    args = utcaArgs(inputFile)
    args += ["--nevents=1000",
             "--no-color",
             "--output-file=%s/compare.root" % outputDir,
             ]
    cmd = oneRun(args, outputFile="%s/comparison.txt" % outputDir)
    return commandOutput(cmd)


def report(d={}, subject=""):
    print subject
    if d.get("stderr") or d.get("returncode"):
        cmd = "echo '%s' |& mail -s '%s' %s" % (blob(d),
                                                subject,
                                                os.environ["USER"])
        os.system(cmd)


def runs(runListFile="",
         minimumRun=None,
         maximumRun=None,
         select=lambda x: False,
         ):
    assert runListFile
    runs = filter(lambda x: minimumRun <= x, selectedRuns(select, runListFile))
    if maximumRun:
        runs = filter(lambda x: x <= maximumRun, runs)
    return runs


def go(baseDir="",
       runs=[],
       process=lambda inputFile, outputDir, run: {},
       dependsUpon=[],
       eosPrefix="root://eoscms.cern.ch",
       eosDir="/eos/cms/store/group/comm_hcal/LS1",
       jobCheck="oneRun",
       nProcMax=5,
       ):

    for rootFile in rootFiles(eosDir):
        run = goodRun(rootFile)
        if run not in runs:
            continue

        processes = stdout("ps -ef | grep %s | grep %s" % (os.environ["USER"], jobCheck))
        if nProcMax < len(processes):
            msg = "Already %d processes:" % len(processes)
            msg += "\n".join(processes)
            sys.exit(msg)

        runDir = makeDir(baseDir, run)
        suffix = process.__name__
        ready, procFlag, doneFlag = flags(runDir=runDir,
                                          run=run,
                                          suffix=suffix,
                                          dependsUpon=dependsUpon)
        if ready:
            stdout("touch %s" % procFlag)
            d = process(inputFile="%s/%s/%s" % (eosPrefix, eosDir, rootFile),
                        outputDir=runDir,
                        run=run)
            stdout("rm %s" % procFlag)

            report(d, subject='Run %d: %s' % (run, suffix))
            if not d["returncode"]:
                with open(doneFlag, "w") as f:
                    print >> f, blob(d)


if __name__ == "__main__":
    runListFile = "%s/public/html/runlist.txt" % os.environ["HOME"]
    prepareRunList(dest=runListFile,
                   hcalRuns="http://cmshcalweb01.cern.ch/HCALruns.txt",
                   )

    fiberIdRuns = runs(runListFile=runListFile,
                       minimumRun=214782,
                       select=lambda x: "FiberID" in x,
                       )

    for func, deps in [(gitLog, []),
                       (dumpFibering, []),
                       (compareFibering, ["dumpFibering"]),
                       ]:
        go(baseDir="%s/public/FiberID" % os.environ["HOME"],
           process=func,
           dependsUpon=deps,
           runs=fiberIdRuns,
           )


    utcaRuns = runs(runListFile=runListFile,
                    minimumRun=219866,
                    select=lambda x: ("/HF/" in x) and ("no_utca" not in x),
                    )
    utcaDir = "%s/public/uTCA" % os.environ["HOME"]

    for func in [gitLog, dumpEvents, dumpEventsNoColor, compare]:
        go(baseDir=utcaDir,
           process=func,
           runs=utcaRuns,
           )

    # summary pdf
    def pdf(**_):
        inFiles = sorted(stdout("cd %s; find | grep compare.pdf" % utcaDir))
        cmd = "cd %s" % utcaDir
        cmd += " && gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile=%s/all.pdf " % utcaDir
        cmd += " ".join(inFiles)
        return commandOutput(cmd)

    go(baseDir=utcaDir, process=pdf, runs=utcaRuns[-1:])
