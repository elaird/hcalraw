import os
import subprocess
import sys


def cmssw():
    return "CMSSW_VERSION" in os.environ


def outputDir(directoryName="output"):
    if not os.path.exists(directoryName):
        os.mkdir(directoryName)
    return directoryName


def minutes(orn):
    orbPerSec = 11.1e3
    return orn/orbPerSec/60.0


def commandOutput(cmd=""):
    return subprocess.Popen(cmd, shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            ).communicate()[0].split()


def Swap64(i64 = ""): #//To flip edianness 
    tmp64 = (i64>>56);
    for i in range(1,8):
        tmp64 += ((i64>>(56-8*i)) & 0xff)<<(8*i)
  
    return tmp64


def bail():
    url = "http://root.cern.ch/drupal/content"
    url += "/how-use-use-python-pyroot-interpreter"

    print "Could not find ROOT.py nor CppyyROOT.py"
    print "See", url
    exit()


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
                print "Using", moduleName
            return r
        except ImportError:
            continue

    findROOT()
    try:
        import ROOT as r
        return r
    except ImportError:
        bail()
