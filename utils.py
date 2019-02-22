import os
import subprocess
import sys


def cmssw():
    return "CMSSW_VERSION" in os.environ


def shortList(lst):
    """ see test_transformation.py"""

    s = ""
    hyphen = False

    l = sorted(set(lst))
    for i, fed in enumerate(l):
        if not i:
            s += "%d" % fed
            continue

        last = i == len(l) - 1
        prevFed = l[i - 1]
        if fed == 1 + prevFed:
            if last:
                s += "-%d" % fed
            else:
                hyphen = True
            continue

        if hyphen:
            s += "-%d,%d" % (prevFed, fed)
        else:
            s += ",%d" % fed
        hyphen = False
    return s


def commandOutput(cmd=""):
    return commandOutputFull(cmd="")["stdout"].split()


def commandOutputFull(cmd=""):
    p = subprocess.Popen(cmd, shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         )
    stdout, stderr = p.communicate()
    return {"stdout": stdout, "stderr": stderr, "returncode": p.returncode}


def delete(thing):
    # free up memory (http://wlav.web.cern.ch/wlav/pyroot/memory.html)
    thing.IsA().Destructor(thing)


def bail():
    url = "https://root.cern.ch/how/how-use-pyroot-root-python-bindings"
    sys.exit("Could not find ROOT.py.  See "+url)


def findROOT():
    try:
        libDir = commandOutput("root-config --libdir")[0]
        sys.path.append(libDir)
    except IndexError:
        bail()


def ROOT():
    try:
        import ROOT as r
        r.PyConfig.IgnoreCommandLineOptions = True
        return r
    except ImportError:
        bail()
