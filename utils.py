import os,subprocess,sys

def outputDir(directoryName="output") :
    if not os.path.exists(directoryName):
        os.mkdir(directoryName)
    return directoryName

def minutes(orn) :
    orbPerSec = 11.1e3
    return orn/orbPerSec/60.0

def commandOutput(cmd="") :
    return subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE).communicate()[0].split()

def bail() :
    print "Could not find ROOT.py"
    print "See http://root.cern.ch/drupal/content/how-use-use-python-pyroot-interpreter"
    exit()

def findROOT() :
    try:
        libDir = commandOutput("root-config --libdir")[0]
        sys.path.append(libDir)
    except IndexError:
        bail()

def ROOT() :
    try:
        import ROOT as r
    except ImportError:
        try:
            findROOT()
            import ROOT as r
        except ImportError:
            bail()
    return r
