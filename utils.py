import os
import subprocess
import sys
import printer
from configuration import hw


def cmssw():
    return "CMSSW_VERSION" in os.environ


def coords(fedId, evn, orn, bcn):
    return "FED %4d / EvN 0x%06x (OrN 0x%08x BcN %04d)" % (fedId, evn, orn, bcn)


def shortList(lst):
    # ./look.py 284928 --feds1=1118,HO,a,1119,1111,670
    # ./look.py 284928 --feds1=1118,HO
    # ./look.py 284928 --feds1=1118,1134,1135
    # ./look.py 284928

    s = ""
    hyphen = False

    l = sorted(lst)
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
    url = "http://root.cern.ch/drupal/content"
    url += "/how-use-use-python-pyroot-interpreter"
    sys.exit("Could not find ROOT.py nor CppyyROOT.py.  See "+url)


def findROOT():
    try:
        libDir = commandOutput("root-config --libdir")[0]
        sys.path.append(libDir)
    except IndexError:
        bail()


def ROOT():
    moduleNames = ["ROOT"]
    if not cmssw():
        moduleNames.insert(0, "CppyyROOT")

    for moduleName in moduleNames:
        try:
            exec("import %s as r" % moduleName)
            if moduleName != "ROOT":
                printer.msg("Using "+moduleName)
            r.PyConfig.IgnoreCommandLineOptions = True
            return r
        except ImportError:
            continue

    findROOT()
    try:
        import ROOT as r
        r.PyConfig.IgnoreCommandLineOptions = True
        return r
    except ImportError:
        bail()
