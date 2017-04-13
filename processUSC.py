#!/usr/bin/env python

import os
import sys
import utils


def commandOutput(command):
    d = utils.commandOutputFull(command)
    d["command"] = command
    return d


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
            assert e.errno == 2

    stdout("wget -O %s %s" % (dest, hcalRuns), checkErr=False)


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
    l =  ["cd ~%s/public/hcalraw_pro" % os.environ["USER"]]
    if "cern.ch" in os.environ.get("HOSTNAME", ""):
        l.append("source env/lxplus6.sh")
    return l


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
            "--feds1=uHCAL",
            "--plugins=patterns",
            ]
    return commandOutput(oneRun(args, outputFile))


def compareFibering_vme(inputFile="", outputDir="", run=0):
    return compareFibering(inputFile, outputDir, run, "data/ref_vme_G.txt")


def compareFibering_utca(inputFile="", outputDir="", run=0):
    return compareFibering(inputFile, outputDir, run, "data/ref_utca_G.txt")


def compareFibering(inputFile="", outputDir="", run=0, ref=""):
    assert ref
    summary = ref.replace("data/ref_", "summary_").replace("_G", "")
    cmd = "cat %s/cabled.txt | ./diff.py %s > %s/%s" % (outputDir, ref,
                                                        outputDir, summary)
    return commandOutput(" && ".join(env() + [cmd]))


def utcaArgs(inputFile=""):
    return ["--file1='%s'" % inputFile,
            "--feds1=929 --feds2=721",
            "--identity-map --no-warn-skip16"]


def dumpEventsNoColor(**kargs):
    kargs["color"] = False
    return dumpEvents(**kargs)


def dumpEvents(inputFile="", outputDir="", run=0, n=3, color=True):
    args = utcaArgs(inputFile) + ["--dump=4 --nevents=%d --usc-summer2014" % n]
    outputFile = "%s/%devents.txt" % (outputDir, n)
    if color:
        outputFile = outputFile.replace(".txt", "_color.txt")
    else:
        args.append("--no-color")
    cmd = oneRun(args, outputFile=outputFile)
    return commandOutput(cmd)


def compare(inputFile="", outputDir="", run=0, stem="compare", moreArgs=[]):
    args = utcaArgs(inputFile)
    args += moreArgs
    args += ["--nevents=1000",
             "--no-color",
             "--output-file=%s/%s.root" % (outputDir, stem),
             ]
    cmd = oneRun(args, outputFile="%s/%s.txt" % (outputDir, stem))
    return commandOutput(cmd)


def report(d={}, subject=""):
    print subject
    if d.get("stderr") or d.get("returncode"):
        if os.path.exists("/bin/mail"):
            cmd = "echo '%s' |& mail -s '%s' %s" % (blob(d),
                                                    subject,
                                                    os.environ["USER"])
            os.system(cmd)
        else:
            print blob(d)


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
       urlPrefix="http://cmsdoc.cern.ch",
       jobCheck="oneRun",
       nProcMax=5,
       debug=False,
       ):

    not_found = []
    for run in runs:
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

        if debug:
            print run, ready, procFlag, doneFlag, process

        if ready:
            fileName = "/store/group/dpg_hcal/comm_hcal/USC/USC_%d.root" % run
            if utils.commandOutputFull("eos stat %s" % fileName)["returncode"]:
                not_found.append(run)
                continue
            else:
                fileName = "root://eoscms.cern.ch/%s" % fileName

            stdout("touch %s" % procFlag)
            d = process(inputFile=fileName,
                        outputDir=runDir,
                        run=run)
            stdout("rm %s" % procFlag)

            urlSuffix = runDir[7+runDir.find("public/"):]
            url = "%s/~%s/%s" % (urlPrefix, os.environ["USER"], urlSuffix)
            report(d, subject='Run %d: %s (%s)' % (run, suffix, url))
            if not d["returncode"]:
                with open(doneFlag, "w") as f:
                    print >> f, blob(d)

    if not_found:
       print "Runs not found in EOS:"
       print not_found


def extraRuns(fileName=""):
    out = []
    if not os.path.exists(fileName):
        return out

    f = open(fileName)
    for iLine, line in enumerate(f):
        if line and line[0] == "#":
            continue

        fields = line.split()
        if len(fields) != 1:
            print "len(fields) %d != 1 in line %d of '%s'" % (len(fields), 1 + iLine, fileName)
            continue
        try:
            out.append(int(fields[0]))
        except ValueError:
            print "Could not determine run number in line %d of '%s'." % (1 + iLine, fileName)
            continue

    f.close()
    return out


if __name__ == "__main__":
    runListFile = "%s/public/html/runlist.txt" % os.environ["HOME"]
    prepareRunList(dest=runListFile,
                   hcalRuns="http://cmshcalweb01.cern.ch/HCALruns.txt",
                   )

    fiberIdRuns = runs(runListFile=runListFile,
                       minimumRun=236631,
                       select=lambda x: "FiberID" in x,
                       ) + extraRuns("%s/public/FiberID/extraruns.txt" % os.environ["HOME"])

    for func, deps in [(dumpFibering, []),
                       (compareFibering_vme, ["dumpFibering"]),
                       (compareFibering_utca, ["dumpFibering"]),
                       ]:
        go(baseDir="%s/public/FiberID" % os.environ["HOME"],
           process=func,
           dependsUpon=deps,
           runs=fiberIdRuns + [],
           )


    sys.exit()
    utcaRuns = runs(runListFile=runListFile,
                    minimumRun=219866,
                    select=lambda x: ("/HF/" in x) and ("no_utca" not in x) and ("SelfTrigger" not in x),
                    )
    utcaDir = "%s/public/uTCA" % os.environ["HOME"]

    for func in [#gitLog,
                 dumpEvents,
                 dumpEventsNoColor,
                 compare,
                 ]:
        go(baseDir=utcaDir,
           process=func,
           runs=utcaRuns+[],
           )

    # summary pdf
    def pdf(**_):
        inFiles = sorted(stdout("cd %s; find | grep compare.pdf" % utcaDir))
        cmd = "cd %s" % utcaDir
        cmd += " && gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile=%s/all.pdf " % utcaDir
        cmd += " ".join(inFiles)
        return commandOutput(cmd)

    go(baseDir=utcaDir, process=pdf, runs=utcaRuns[-1:])
