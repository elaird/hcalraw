import utils
r = utils.ROOT()

from configuration import sw
import os
import printer
import sys


def setup_root():
    r.gROOT.SetBatch(True)

    load_libs = False
    if r.gROOT.GetVersionInt() < 60000:  # before ROOT6
        r.gROOT.SetStyle("Plain")
        r.gStyle.SetPalette(1)
        load_libs = True

    if not utils.cmssw():
        load_libs = True

    if load_libs:
        for lib in ["cdf", "cms"]:
            if r.gSystem.Load("%s/cpp/%s.so" % (os.environ["PWD"], lib)) < 0:
                sys.exit("Try this:\ncd cpp; make -j 5; cd -")
    else:
        # FIXME
        r.gInterpreter.SetClassAutoloading(False)
        if not hasattr(r, "CDFChunk2"):
            r.gInterpreter.ProcessLine('#include "cpp/cdf.h"')
        if not hasattr(r, "FEDRawDataWords"):
            r.gInterpreter.ProcessLine('#include "cpp/cms.h"')
        # r.gInterpreter.ProcessLine('#include "cpp/FEDRawData.cc"')
        # r.gInterpreter.ProcessLine('#include "cpp/FEDRawDataCollection.h"')

    if sw.use_fwlite and utils.cmssw():
        r.gSystem.Load("libFWCoreFWLite.so")
        r.AutoLibraryLoader.enable()

        libs = ["DataFormatsFEDRawData"]
        if os.environ["CMSSW_RELEASE_BASE"]:
            base = os.environ["CMSSW_RELEASE_BASE"]
        else:
            base = os.environ["CMSSW_BASE"]
        libPath = "/".join([base, "lib", os.environ["SCRAM_ARCH"]])
        r.gSystem.SetLinkedLibs(" -L"+libPath+" -l".join([""]+libs))
    else:
        # TClass::TClass:0: RuntimeWarning: no dictionary for class x::y::z is available
        r.gErrorIgnoreLevel = r.kError


def tchain(spec, cacheSizeMB=None):
    chain = r.TChain(spec["treeName"])
    for fileName in spec["fileNames"]:
        chain.Add(fileName)

    if cacheSizeMB:
        chain.SetCacheSize(cacheSizeMB * 1024**2)

    if spec["treeName"] == "Events":  # CMS CDAQ
        chain.SetBranchStatus("*", 0)
        found = False
        for branch in spec["rawCollections"]:
            if sw.use_fwlite:
                for suffix in [".obj", ".present"]:
                    branch1 = branch + suffix
                    if chain.GetBranch(branch1):
                        chain.SetBranchStatus(branch1, 1)
                        found = True
                    else:
                        printer.info("Could not find branch %s" % branch1)
            else:
                if chain.GetBranch(branch):
                    chain.SetBranchStatus(branch, 1)
                    found = True
                else:
                    printer.info("Could not find branch %s" % branch)
            if found:
                spec["rawCollection"] = branch
                break

        if not found:
            sys.exit("Could not find any branches: see configuration/sw.py")

    return chain


def pruneFeds(chain, s):
    wargs = {}

    remove = {}
    for fedId in s["fedIds"]:
        wargs[fedId] = {"tree": chain}
        if s["treeName"] == "Events":  # CMS CDAQ
            wfunc = wordsOneFed
            wargs[fedId].update({"fedId": fedId,
                                 "collection": s["rawCollection"],
                                 "product": sw.use_fwlite})
        elif s["treeName"] == "CMSRAW":  # HCAL local
            wfunc = wordsOneChunk
            wargs[fedId]["branch"] = s["branch"](fedId)
        else:
            wfunc = wordsOneBranch
            wargs[fedId]["branch"] = s["branch"](fedId)

        raw = wfunc(**wargs[fedId])
        if not raw:
            remove[fedId] = "no branch %s" % wargs[fedId].get("branch")
        elif not raw.size():
            remove[fedId] = "read zero bytes"

    for fedId, msg in sorted(remove.items()):
        del wargs[fedId]
        # printer.warning("removing FED %4d from spec (%s)." % (fedId, msg))
    if remove:
        printer.info("No data from FED%s %s" % ("s" if 2 <= len(remove) else "", utils.shortList(remove.keys())))

    if wargs:
        del s["fedIds"]
        s["fedId0"] = sorted(wargs.keys())[0]
        for v in ["wfunc", "wargs"]:
            s[v] = eval(v)
    elif s["treeName"] == "Events":
        sys.exit("No listed FEDs had any data.")
    else:
        sys.exit(branches(chain))


def charsOneFed(tree=None, fedId=None, collection="", product=None):
    FEDRawData = getattr(tree, collection)
    if product:
        FEDRawData = FEDRawData.product()
    return r.FEDRawDataChars(FEDRawData.FEDData(fedId))


def wordsOneFed(tree=None, fedId=None, collection="", product=None):
    FEDRawData = getattr(tree, collection)
    if product:
        FEDRawData = FEDRawData.product()
    return r.FEDRawDataWords(FEDRawData.FEDData(fedId))


def wordsOneChunk(tree=None, branch=""):
    chunk = wordsOneBranch(tree, branch)
    if chunk is None:
        return chunk
    else:
        return r.CDFChunk2(chunk)


def wordsOneBranch(tree=None, branch=""):
    try:
        chunk = getattr(tree, branch)
    except AttributeError:
        chunk = None
    return chunk


def branches(tree):
    names = [item.GetName() for item in tree.GetListOfBranches()]
    msg = ["These branches are available:"] + sorted(names)
    return "\n".join(msg)
