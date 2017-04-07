import os
import struct
import sys
import time
import utils

r = utils.ROOT()
import autoBook
from configuration import hw, sw
import decode
import printer
import plugins


def setup(plugin_names=[]):
    r.gROOT.SetBatch(True)

    if r.gROOT.GetVersionInt() < 60000:  # before ROOT6
        for lib in [ "cdf", "cms"]:
            if r.gSystem.Load("%s/cpp/%s.so" % (os.environ["PWD"], lib)):
                sys.exit("Try this:\ncd cpp; make -j 5; cd -")
        r.gROOT.SetStyle("Plain")
    else:
        r.gInterpreter.SetClassAutoloading(False)
        r.gInterpreter.ProcessLine('#include "cpp/cdf.h"')
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

    for p in plugin_names:
        exec("from plugins import %s" % p)


def coords(d):
    h = d["header"]
    return h["EvN"], h["OrN"], h["BcN"]


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


def chainLoopSparse(chain, nEntries, callback, nPerTree, progress=False):
    iMask = 0
    iTreeFirstEntry = 0
    nSeen = 0

    for nTree in range(chain.GetNtrees()):
        if chain.LoadTree(iTreeFirstEntry) < 0:
            return

        tree = chain.GetTree()
        if not tree:
            continue

        nTreeEntries = tree.GetEntries()
        for iTreeEntry in range(nTreeEntries):
            # if (not nTree) and iTreeEntry == 100:
            #     tree.StopCacheLearningPhase()

            if nPerTree <= iTreeEntry:
                break

            tree.GetEntry(iTreeEntry)  # fixme: protect?
            entry = iTreeFirstEntry + iTreeEntry
            nSeen += 1
            # print "nTree %d  iTreeEntry %d   entry %d   nSeen %d" % (nTree, iTreeEntry, entry, nSeen)

            if callback(chain, entry):
                return

            if progress:
                iMask = reportProgress(entry, nSeen, iMask)

            if nEntries != None and nEntries <= nSeen:
                return

        # tree.PrintCacheStats()
        iTreeFirstEntry += nTreeEntries


def chainLoop(chain, iEntryStart, iEntryStop, callback, progress=False, sparseLoop=None):
    if 0 <= sparseLoop:
        chainLoopSparse(chain, iEntryStop, callback, sparseLoop, progress=progress)
        return

    iMask = 0

    iEntry = iEntryStart
    while iEntry != iEntryStop:
        if chain.GetEntry(iEntry) <= 0:
            break
        if callback(chain, iEntry):
            break

        iEntry += 1
        if progress:
            iMask = reportProgress(iEntry, iEntry - iEntryStart, iMask)


def pruneFeds(chain, s, uargs):
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
        if raw:
            if not unpacked(fedData=raw, **uargs).get("nBytesSW"):
                remove[fedId] = "read zero bytes"
        else:
            remove[fedId] = "no branch %s" % wargs[fedId].get("branch")

    for fedId, msg in sorted(remove.iteritems()):
        del wargs[fedId]
        # printer.warning("removing FED %4d from spec (%s)." % (fedId, msg))
    if remove:
        printer.warning("No data from FEDs %s" % (",".join(["%d" % fedId for fedId in sorted(remove.keys())])))

    if wargs:
        del s["fedIds"]
        s["fedId0"] = sorted(wargs.keys())[0]
        for v in ["wfunc", "wargs"]:
            s[v] = eval(v)
    elif s["treeName"] == "Events":
        sys.exit("No listed FEDs had any data.")
    else:
        sys.exit(branches(chain))


def fillEventMap(iEntry, raw, forward, forwardBcn, backward):
    evn, orn, bcn = coords(raw)
    evnOrn = (evn, orn)

    forward[iEntry] = evnOrn
    forwardBcn[iEntry] = bcn
    backward[evnOrn] = iEntry


# this function returns two dictionaries,
# one maps TTree entry to (orn, evn)
# the other maps the reverse
def eventMaps(chain, s={}, identityMap=False):
    forward = {}
    backward = {}
    forwardBcn = {}

    if s["progress"]:
        print "Mapping %s:" % s["label"]

    kargs = {"headerOnly": True,
             "nBytesPer": s["nBytesPer"],
             "skipWords64": s["skipWords64"],
            }

    try:
        def fillEventMap2(chain, iEntry):
            if iEntry == nMapMin:
                pruneFeds(chain, s, kargs)

            wargs = s["wargs"][s["fedId0"]]
            raw = unpacked(fedData=s["wfunc"](**wargs), **kargs)
            return fillEventMap(iEntry, raw, forward, forwardBcn, backward)

        nMapMin = 0     # start from beginning
        nMapMax = None  # look at all entries

        nEv = s["nEventsMax"] + s["nEventsSkip"]
        if nEv:
            if identityMap:
                nMapMin = s["nEventsSkip"]
                nMapMax = nEv
            else:
                nMapMax = nEv * 2  # a guess for how far to look not to miss out-of-order events

        chainLoop(chain, nMapMin, nMapMax, fillEventMap2, progress=s["progress"], sparseLoop=s["sparseLoop"])
    except KeyboardInterrupt:
        printer.warning("KeyboardInterrupt in eventMaps()")

    return forward, backward, forwardBcn


def reportProgress(globalEntry, iEvent, iMask):
    if iEvent and not (iEvent & (2**iMask - 1)):
        msg = "%8d %s" % (iEvent, time.ctime())
        if globalEntry != iEvent:
            msg += "  (entry %8d)" % globalEntry
        print msg
        return iMask + 1
    else:
        return iMask


def outerInnerCompare(chain, oEntry, outer, inner, innerEvent, chainI, kargs):
    kargs["raw1"] = collectedRaw(tree=chain, specs=outer)

    if innerEvent:
        iEntry = innerEvent[oEntry]
        if iEntry is None:
            oEntry += 1
            return

        if chainI.GetEntry(iEntry) <= 0:
            return True  # break!

    if inner:
        kargs["raw2"] = collectedRaw(tree=chainI, specs=inner)

    if not outer["unpack"]:
        return

    for p in outer["plugins"]:
        f = getattr(eval("plugins.%s" % p), p)
        f(**kargs)


def loop(chain=None, chainI=None, outer={}, inner={}, innerEvent={}, options={}):
    if outer["progress"]:
        print "Looping:"

    kargs = {"book": autoBook.autoBook("book")}
    kargs.update(options)

    try:
        def outerInnerCompare2(chain, iEntry):
            return outerInnerCompare(chain, iEntry, outer, inner, innerEvent, chainI, kargs)

        nMin = outer["nEventsSkip"]
        nMax = (outer["nEventsSkip"] + outer["nEventsMax"]) if outer["nEventsMax"] else None
        chainLoop(chain, nMin, nMax, outerInnerCompare2,
                  progress=outer["progress"], sparseLoop=outer["sparseLoop"])

    except KeyboardInterrupt:
        printer.warning("KeyboardInterrupt in loop()")

    return kargs["book"]


def collectedRaw(tree=None, specs={}):
    raw = {}
    kargs = {}
    for item in ["dump", "unpack", "nBytesPer", "skipWords64"]:
        kargs[item] = specs[item]

    for fedId, wargs in sorted(specs["wargs"].iteritems()):
        raw[fedId] = unpacked(fedData=specs["wfunc"](**wargs),
                              warn=specs["warnUnpack"],
                              **kargs)

    raw[None] = {"iEntry": tree.GetReadEntry()}
    for key in ["label", "dump", "crateslots"]:
        raw[None][key] = specs[key]

    return raw


def w64(fedData, jWord64, nBytesPer):
    if nBytesPer == 1:
        offset = 8*jWord64
        bytes = [fedData.at(offset+iByte) for iByte in range(8)]
        word64 = struct.unpack('Q', "".join(bytes))[0]
        #like above with 'B'*8 rather than 'Q':
        #b = [ord(fedData.at(offset+iByte)) for iByte in range(8)]
    elif nBytesPer == 4:
        word64 = fedData.at(2*jWord64)
        word64 += fedData.at(2*jWord64 + 1) << 32
    elif nBytesPer == 8:
        word64 = fedData.at(jWord64)
    return word64


# for format documentation, see decode.py
def unpacked(fedData=None, nBytesPer=None, headerOnly=False, unpack=True,
             warn=True, skipWords64=[], dump=-99):
    assert fedData
    assert nBytesPer in [1, 4, 8], "ERROR: invalid nBytes per index (%s)." % str(nBytesPer)

    header = {"iWordPayload0": 6,
              "utca": None,
              }  # modified by decode.header
    trailer = {}
    other = {}
    htrBlocks = {}

    nWord64Trailer = 1

    nWord64 = fedData.size()*nBytesPer/8
    nWord16Skipped = 0

    nToSkip = len(set(skipWords64))
    skipped64 = []

    for jWord64 in range(nWord64):
        if not unpack:
            continue

        word64 = w64(fedData, jWord64, nBytesPer)

        if jWord64 in skipWords64:
            skipped64.append(word64)
            continue

        iWord64 = jWord64 - len(skipped64)

        if 9 <= dump:
            if not iWord64:
                print "#iw64 w64"
            print "%5d" % iWord64, "%016x" % word64

        if iWord64 < header["iWordPayload0"]:
            decode.header(header, iWord64, word64)
            if header.get("uFoV"):
                nWord64Trailer = 2  # accommodate block trailer
            iWordTrailer0 = nWord64 - nToSkip - nWord64Trailer
        elif headerOnly:
            break
        elif iWord64 < iWordTrailer0:
            for i in range(4):
                word16 = (word64 >> (16*i)) & 0xffff
                iWord16 = 4*iWord64+i
                returnCode = decode.payload(htrBlocks,
                                            iWord16=iWord16,
                                            word16=word16,
                                            word16Counts=header["word16Counts"],
                                            utca=header["utca"],
                                            fedId=header["FEDid"],
                                            warn=warn,
                                            dump=dump)
                if returnCode is None:
                    continue

                # ignore VME pad words (zero)
                if not header["utca"] and iWord64 + 1 == iWordTrailer0:
                    if 4 * header["iWordPayload0"] + sum(header["word16Counts"]) <= iWord16:
                        if not word16:
                            continue

                nWord16Skipped += 1
                if warn:
                    printer.warning(" ".join(["skipping",
                                              "FED %d" % header["FEDid"],
                                              "event %d" % header["EvN"],
                                              "iWord16 %d" % iWord16,
                                              "word16 0x%04x" % word16,
                                              ]))
        else:
            if "htrIndex" in htrBlocks:
                del htrBlocks["htrIndex"]  # fixme

            if header["uFoV"] and (iWord64 == nWord64 - nToSkip - 2):
                decode.block_trailer_ufov1(trailer, iWord64, word64)
            else:
                decode.trailer(trailer, iWord64, word64)

    decode.other(other, skipped64)

    return {"header": header,
            "trailer": trailer,
            "htrBlocks": htrBlocks,
            "other": other,
            "nBytesSW": 8*nWord64,
            "nWord16Skipped": nWord16Skipped,
            }


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


def inner_vars(outer, inner, mapOptions, oMapF, oMapB, oMapBcn):
    iMapF = iMapB = iMapBcn = {}
    if inner.get("fileNames") == outer["fileNames"]:
        chainI = chain
        innerEvent = {}
    elif inner:
        chainI = tchain(inner)
        if mapOptions["identityMap"]:
            iMapF = oMapF
            iMapB = oMapB
            iMapBcn = oMapBcn
        else:
            iMapF, iMapB, iMapBcn = eventMaps(chainI, inner)

        innerEvent = eventToEvent(oMapF, iMapB)
        if set(innerEvent.values()) == set([None]):
            sys.exit("No common events found.  Consider passing --identity-map.")

        if mapOptions['printEventMap']:
            for oEntry, iEntry in sorted(innerEvent.iteritems()):
                printer.msg(", ".join(["oEntry = %s" % str(oEntry),
                                       "oEvnOrn = %s" % str(oMapF[oEntry]),
                                       "iEntry = %s" % str(iEntry),
                                       ]))
    else:
        chainI = None
        innerEvent = {}

    return chainI, innerEvent, iMapF, iMapB, iMapBcn


def category_vs_time(oMap={}, oMapBcn={}, iMap={}, iMapBcn={}, innerEvent={}):
    d = {}
    for oEntry, (evn, orn) in oMap.iteritems():
        bcn = oMapBcn[oEntry]
        time = utils.minutes(orn, bcn)
        if innerEvent.get(oEntry) is not None:
            d[time] = (3, evn, orn, bcn)
        else:
            d[time] = (2, evn, orn, bcn)

    iEntries = innerEvent.values()
    for iEntry, (evn, orn) in iMap.iteritems():
        if iEntry in iEntries:
            continue
        bcn = iMapBcn[iEntry]
        time = utils.minutes(orn, bcn)
        d[time] = (1, evn, orn, bcn)

    return d


def write_category_graphs(d={}, outer={}, inner={}):
    for iGraph, gr in enumerate(graphs(d, oFed=outer["fedId0"], iFed=inner.get("fedId0", None))):
        if iGraph == 0:
            gr.SetTitle("_".join(["only %s" % inner.get("label", ""), "only %s" % outer.get("label", ""), "both"]))
        if iGraph == 1:
            gr.SetTitle(",".join(outer["fileNames"]))
        gr.Write()


def graphs(d={}, oFed=None, iFed=None):
    gr1 = r.TGraph()
    gr2 = r.TGraph()
    gr3 = r.TGraph()
    gr4 = r.TGraph()

    suffix = ""
    for fed in [oFed, iFed]:
        if fed is not None:
            suffix += "_%d" % fed

    gr1.SetName("category_vs_time" + suffix)
    gr2.SetName("evn_vs_time" + suffix)
    gr3.SetName("bcn_delta_vs_time" + suffix)
    gr4.SetName("incr_evn_vs_time" + suffix)

    evn0 = orn0 = bcn0 = None
    for i, time in enumerate(sorted(d.keys())):
        category, evn, orn, bcn = d[time]
        gr1.SetPoint(i, time, category)
        gr2.SetPoint(i, time, evn)
        if orn0 is not None:
            gr3.SetPoint(i, time, hw.nBx * (orn - orn0) + (bcn - bcn0))
            gr4.SetPoint(i, time, evn0 < evn)
        else:
            gr3.SetPoint(i, time, 1.0e30)
            gr4.SetPoint(i, time, 1)
        evn0 = evn
        orn0 = orn
        bcn0 = bcn
    return gr1, gr2, gr3, gr4


def eventToEvent(mapF={}, mapB={}):
    out = {}
    for oEntry, evnOrn in mapF.iteritems():
        out[oEntry] = None
        if evnOrn in mapB:
            out[oEntry] = mapB[evnOrn]
    return out


def go(outer={}, inner={}, outputFile="",
       mapOptions={}, loopOptions={},
       printEventSummary=None):

    chain = tchain(outer)
    oMapF, oMapB, oMapBcn = eventMaps(chain, outer, mapOptions["identityMap"])
    chainI, innerEvent, iMapF, iMapB, iMapBcn = inner_vars(outer, inner, mapOptions,
                                                           oMapF, oMapB, oMapBcn)
    book = loop(chain=chain, chainI=chainI,
                outer=outer, inner=inner,
                innerEvent=innerEvent,
                options=loopOptions)

    utils.delete(chain)
    if chainI:
        utils.delete(chainI)

    # write results to a ROOT file
    dirName = os.path.dirname(outputFile)
    if not os.path.exists(dirName):
        print "Creating directory '%s'" % dirName
        os.mkdir(dirName)

    f = r.TFile(outputFile, "RECREATE")
    if not f.IsZombie():
        write_category_graphs(category_vs_time(oMap=oMapF, oMapBcn=oMapBcn,
                                               iMap=iMapF, iMapBcn=iMapBcn,
                                               innerEvent=innerEvent),
                              outer,
                              inner)
        for h in book.values():
            h.Write()
    f.Close()

    for h in book.values():
        utils.delete(h)

    if printEventSummary:
        s = "%s: %4s = %6d" % (outputFile, outer["label"], len(oMapF))
        if inner:
            nBoth = len(filter(lambda x: x is not None, innerEvent.values()))
            s += ", %4s = %6d, both = %6d" % (inner["label"], len(iMapB), nBoth)
        printer.msg(s)

    return not len(oMapF)


def printChannelSummary(outputFile):
    f = r.TFile(outputFile)

    hs = []
    for name in ["MatchedFibersCh%d" % i for i in range(3)] + ["MatchedTriggerTowers"]:
        h = f.Get(name)
        if h:
            hs.append(h)

    lines = []
    if hs:
        words = ["nMatched"]
        words += ["FibCh%d" % i for i in range(3)]
        words.append("  TPs")
        words = "   ".join(words)
        lines.append(words)
        lines.append("-" * len(words))
    else:
        return

    for iBin in range(0, 2 + hs[0].GetNbinsX()):
        xs = [h.GetBinCenter(iBin) for h in hs]
        if len(set(xs)) != 1:
            printer.error("binnings for nMatched do not match.")
            return

        for h in hs:
            w = h.GetBinWidth(iBin)
            if 1.0e-6 < abs(w - 1.0):
                printer.warning("Histogram %s bin %d has width %g" % (h.GetName(), iBin, w))

        x = xs[0]
        cs = [h.GetBinContent(iBin) for h in hs]

        if any(cs):
            s = ["   %4d" % x]
            s += ["%4d" % c for c in cs]
            lines.append("     ".join(s))

    if len(lines) > 12:
        printer.info("suppressed printing of match histogram (more than 10 different occupancies)")
    else:
        for line in lines:
            print line

    f.Close()


def bail(specs, fileName):
    n = max([len(spec["treeName"]) for spec in specs])
    fmt = "%" + str(n) + "s: %s\n"

    lst = []
    for spec in specs:
        name = spec["treeName"]
        del spec["treeName"]
        lst.append((name, spec))

    msg = "found %s != 1 known TTrees in file %s\n" % (len(specs), fileName)
    for name, spec in sorted(lst):
        msg += fmt % (name, str(spec))
    sys.exit(msg)


def fileSpec(fileNames=[]):
    f = r.TFile.Open(fileNames[0])
    if (not f) or f.IsZombie():
        sys.exit("File %s could not be opened." % fileNames[0])

    treeNames = []
    for tkey in f.GetListOfKeys():
        obj = f.Get(tkey.GetName())
        if obj.ClassName() == "TTree":
            treeNames.append(obj.GetName())
    f.Close()

    specs = []
    for treeName in set(treeNames):  # set accomodate cycles, e.g. CMSRAW;3 CMSRAW;4
        spec = sw.format(treeName)
        if spec:
            spec["fileNames"] = fileNames
            spec["treeName"] = treeName
            specs.append(spec)

    if len(specs) != 1:
        bail(specs, fileName[0])
    else:
        return specs[0]


def oneRun(files1=[],
           feds1=[],
           files2=[],
           feds2=[],
           mapOptions={},
           compareOptions={},
           printOptions={},
           noUnpack=False,
           nEvents=None,
           nEventsSkip=None,
           sparseLoop=None,
           outputFile="",
           plugins=[],
           ):

    assert files1
    assert feds1

    common = {"nEventsMax": nEvents,
              "nEventsSkip": nEventsSkip,
              "sparseLoop": sparseLoop,
              "unpack": not noUnpack,
              "plugins": plugins,
              }
    common.update(printOptions)

    spec1 = fileSpec(files1)
    spec1.update(common)
    spec1.update({"fedIds": feds1,
                  "label": "files1",
                  })
    inner = {}

    if files2:
        if not feds2:
            sys.exit("files2 '%s' but feds2 %s" % (files2, feds2))
        spec2 = fileSpec(files2)
        spec2.update(common)
        spec2.update({"fedIds": feds2,
                      "label": "files2",
                      })
        inner = spec2


    loopOptions = {"warnQuality": printOptions["warnQuality"]}
    loopOptions.update(compareOptions)

    return go(outer=spec1,
              inner=inner,
              outputFile=outputFile,
              mapOptions=mapOptions,
              loopOptions=loopOptions,
              printEventSummary=("compare" in plugins) and feds2 and (files1 != files2) and 0 <= common["dump"],
              )
