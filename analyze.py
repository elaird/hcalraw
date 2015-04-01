import os
import struct
import sys
import time
import utils

r = utils.ROOT()
import autoBook
import compare
import configuration
import decode
import printer


def setup():
    r.gROOT.SetBatch(True)
    r.gSystem.Load("cpp/cdf.so")
    r.gSystem.Load("cpp/cms.so")

    if configuration.use_fwlite and utils.cmssw():
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


def nEvents(tree, nMax):
    assert tree
    nEntries = tree.GetEntries()
    return min(nEntries, nMax) if (nMax is not None) else nEntries


def coords(d):
    h = d["header"]
    return h["OrN"], h["BcN"], h["EvN"]


# this function returns two dictionaries,
# one maps TTree entry to (orn, evn)
# the other maps the reverse
def eventMaps(s={}, options={}):
    fileName = s["fileName"]
    treeName = s["treeName"]
    assert fileName
    assert treeName

    nEventsMax = s["nEventsMax"]
    if treeName != "Events":
        fedId0 = s["fedIds"][0]
        branch0 = s["branch"](fedId0)

    forward = {}
    backward = {}

    f = r.TFile.Open(fileName)
    if (not f) or f.IsZombie():
        sys.exit("File %s could not be opened." % fileName)

    tree = f.Get(treeName)
    if not tree:
        f.ls()
        sys.exit("tree %s not found.  The above objects are available." % treeName)

    if s["progress"]:
        iMask = 0
        print "Mapping %s:" % s["label"]

    kargs = {"headerOnly": True,
             "nBytesPer": s["nBytesPer"]}
    if treeName == "mol":
        kargs["skipWords64"] = [0, 1]

    for iEvent in range(nEvents(tree, nEventsMax)):
        tree.GetEntry(iEvent)
        orn = bcn = evn = None

        if treeName == "Events":  # CMS CDAQ
            fedId0 = s["fedIds"][0]
            rawThisFed = wordsOneFed(tree=tree,
                                     fedId=fedId0,
                                     collection=s["rawCollection"],
                                     product=s["product"]
                                 )
        elif treeName == "CMSRAW":  # HCAL local
            rawThisFed = wordsOneChunk(tree=tree, branch=branch0)
        else:
            rawThisFed = wordsOneBranch(tree=tree, branch=branch0)

        raw = unpacked(fedData=rawThisFed, **kargs)
        if not raw["nBytesSW"]:
            printer.error("the first listed FED (%d) has zero bytes in tree '%s'." % (fedId0, treeName))
            sys.exit(2)

        if s["progress"]:
            iMask = progress(iEvent, iMask)

        orn, bcn, evn = coords(raw)

        t = (orn, evn)

        forward[iEvent] = t
        backward[t] = iEvent

    f.Close()
    if s["progress"]:
        print
    return forward, backward


def progress(iEvent, iMask):
    if iEvent and not (iEvent & (2**iMask - 1)):
        print "%8d" % iEvent, time.ctime()
        return iMask + 1
    else:
        return iMask


def loop(inner={}, outer={}, innerEvent={}, book={}, compareOptions={}, cacheSizeMB=None):
    if inner:
        fI = r.TFile.Open(inner["fileName"])
        treeI = fI.Get(inner["treeName"])
        assert treeI, inner["treeName"]
        if cacheSizeMB:
            treeI.SetCacheSize(cacheSizeMB * 1024**2)

    f = r.TFile.Open(outer["fileName"])
    tree = f.Get(outer["treeName"])
    assert tree, outer["treeName"]
    if cacheSizeMB:
        tree.SetCacheSize(cacheSizeMB * 1024**2)

    if outer["progress"]:
        iMask = 0
        print "Looping:"

    kargs = {"book": book}
    kargs.update(compareOptions)

    for iOuterEvent in range(outer["nEventsSkip"],
                             nEvents(tree, outer["nEventsMax"])):
        nb = tree.GetEntry(iOuterEvent)
        if nb <= 0:
            continue

        if outer["progress"]:
            iMask = progress(iOuterEvent, iMask)

        kargs["raw1"] = collectedRaw(tree=tree, specs=outer)

        if inner:
            iInnerEvent = innerEvent[iOuterEvent]
            if (iInnerEvent is None) or (treeI.GetEntry(iInnerEvent) <= 0):
                continue
            kargs["raw2"] = collectedRaw(tree=treeI, specs=inner)

        if outer["unpack"]:
            compare.compare(**kargs)

    f.Close()
    if inner:
        fI.Close()


def collectedRaw(tree=None, specs={}):
    raw = {}
    kargs = {}
    for item in ["patterns", "warn", "dump", "unpack", "nBytesPer"]:
        kargs[item] = specs[item]

    if specs["treeName"] == "mol":
        kargs["skipWords64"] = [0, 1]
        kargs["decodeSkipped64"] = decode.molHeader

    for fedId in specs["fedIds"]:
        if "branch" in specs:
            branch = specs["branch"](fedId)

        if specs["treeName"] == "Events":
            rawThisFed = wordsOneFed(tree, fedId, specs["rawCollection"], specs["product"])
        elif specs["treeName"] == "CMSRAW":
            rawThisFed = wordsOneChunk(tree, branch)
        else:
            rawThisFed = wordsOneBranch(tree=tree, branch=branch)

        raw[fedId] = unpacked(fedData=rawThisFed, **kargs)

        if not raw[fedId]["nBytesSW"]:
            printer.warning("removing FED %d from spec (read zero bytes)." % fedId)
            del raw[fedId]
            specs["fedIds"].remove(fedId)
            continue

    raw[None] = {"iEntry": tree.GetReadEntry()}
    for key in ["label", "patterns", "dump", "crateslots"]:
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
             warn=True, skipWords64=[], decodeSkipped64=None, patterns=False, dump=-99):
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
        word64 = w64(fedData, jWord64, nBytesPer)

        if jWord64 in skipWords64:
            skipped64.append(word64)
            continue

        iWord64 = jWord64 - len(skipped64)

        if 7 <= dump:
            if not iWord64:
                print "#iw64 w64"
            print "%5d" % iWord64, "%016x" % word64

        if not unpack:
            continue

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
                                            patterns=patterns,
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

    if decodeSkipped64:
        decodeSkipped64(other, skipped64)

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
    return r.CDFChunk2(chunk)


def wordsOneBranch(tree=None, branch=""):
    try:
        chunk = getattr(tree, branch)
    except AttributeError:
        msg = ["Branch %s not found.  These branches are available:" % branch]
        names = [item.GetName() for item in tree.GetListOfBranches()]
        msg += sorted(names)
        sys.exit("\n".join(msg))
    return chunk


def evn_vs_time(values=[]):
    gr = r.TGraph()
    gr.SetName("evn_vs_time")
    for i, (orn, evn) in enumerate(sorted(values)):
        gr.SetPoint(i, utils.minutes(orn), evn)
    return gr


def category_vs_orn(oMap={}, iMap={}, innerEvent={}):
    d = {}
    for oEvent, ornEvn in oMap.iteritems():
        orn = ornEvn[0]
        if oEvent in innerEvent and (innerEvent[oEvent] is not None):
            d[orn] = 3
        else:
            d[orn] = 2

    iEvents = innerEvent.values()
    for iEvent, ornEvn in iMap.iteritems():
        if iEvent in iEvents:
            continue
        orn = ornEvn[0]
        d[orn] = 1

    return d


def graph(d={}):
    gr = r.TGraph()
    gr.SetName("category_vs_time")
    for i, key in enumerate(sorted(d.keys())):
        gr.SetPoint(i, utils.minutes(key), d[key])
    return gr


def eventToEvent(mapF={}, mapB={}, options={}):
    out = {}
    for oEvent, ornEvn in mapF.iteritems():
        out[oEvent] = None
        if ornEvn in mapB:
            # fixme: check for multiple matches
            out[oEvent] = mapB[ornEvn]
    return out


def go(outer={}, inner={}, outputFile="",
       mapOptions={}, compareOptions={},
       printEventSummary=None, printChannelSummary=None):

    innerEvent = {}
    deltaOrn = {}

    oMapF, oMapB = eventMaps(outer)
    iMapF = iMapB = {}

    if inner:
        iMapF, iMapB = eventMaps(inner)
        innerEvent = eventToEvent(oMapF, iMapB, options=mapOptions)
        if mapOptions.get('identityMap', False):
            for key in innerEvent.keys():
                innerEvent[key] = key
        if set(innerEvent.values()) == set([None]):
            sys.exit("No common events found.  Consider passing --identity-map.")
        if mapOptions.get('printEventMap', False):
            for oEvent, iEvent in sorted(innerEvent.iteritems()):
                printer.msg(", ".join(["oEvent = %s" % str(oEvent),
                                       "oOrnEvn = %s" % str(oMapF[oEvent]),
                                       "iEvent = %s" % str(iEvent),
                                       ]))

    book = autoBook.autoBook("book")
    loop(inner=inner, outer=outer, innerEvent=innerEvent,
         book=book, compareOptions=compareOptions)

    #write results to a ROOT file
    dirName = os.path.dirname(outputFile)
    if not os.path.exists(dirName):
        print "Creating directory '%s'" % dirName
        os.mkdir(dirName)

    f = r.TFile(outputFile, "RECREATE")
    evn_vs_time(oMapF.values()).Write()

    gr = graph(category_vs_orn(oMap=oMapF, iMap=iMapF, innerEvent=innerEvent))
    nBoth = len(filter(lambda x: x is not None, innerEvent.values()))
    labels = ["only %s (%d)" % (inner["label"],
                                len(iMapF)-nBoth) if inner else "",
              "only %s (%d)" % (outer["label"],
                                len(oMapF)-nBoth) if outer else "",
              "both (%d)" % nBoth if inner else "",
              ]
    gr.SetTitle("_".join(labels))
    gr.Write()

    for h in book.values():
        h.Write()
    f.Close()

    if printEventSummary:
        s = "%s: %4s = %6d" % (outputFile, outer["label"], len(oMapF))
        if inner:
            s += ", %4s = %6d, both = %6d" % (inner["label"], len(iMapB), nBoth)
        printer.msg(s)

    if printChannelSummary:
        for iChannel in range(3):
            print "Channel %d:" % iChannel
            printHisto(outputFile, histoName="MatchedFibersCh%d" % iChannel)
            print

        print "TPs:"
        printHisto(outputFile, histoName="MatchedTriggerTowers")
        print


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


def fileSpec(fileName=""):
    f = r.TFile.Open(fileName)
    if (not f) or f.IsZombie():
        sys.exit("File %s could not be opened." % fileName)

    treeNames = []
    for tkey in f.GetListOfKeys():
        obj = f.Get(tkey.GetName())
        if obj.ClassName() == "TTree":
            treeNames.append(obj.GetName())

    specs = []
    for treeName in set(treeNames):  # set accomodate cycles, e.g. CMSRAW;3 CMSRAW;4
        spec = configuration.format(treeName)
        if spec:
            spec["treeName"] = treeName
            specs.append(spec)

    if len(specs) != 1:
        bail(specs, fileName)
    else:
        return specs[0]
    f.Close()


def oneRun(file1="",
           feds1=[],
           file2="",
           feds2=[],
           patterns=False,
           mapOptions={},
           compareOptions={},
           printOptions={},
           noUnpack=False,
           nEvents=None,
           nEventsSkip=None,
           outputFile="",
           ):

    assert file1
    assert feds1

    common = {"nEventsMax": nEvents,
              "nEventsSkip": nEventsSkip,
              "patterns": patterns,
              "unpack": not noUnpack,
              }
    common.update(printOptions)

    spec1 = fileSpec(file1)
    spec1.update(common)
    spec1.update({"fileName": file1,
                  "fedIds": feds1,
                  "label": "file1",
                  })
    inner = {}

    if file2:
        assert feds2
        spec2 = fileSpec(file2)
        spec2.update(common)
        spec2.update({"fileName": file2,
                      "fedIds": feds2,
                      "label": "file2",
                      })
        inner = spec2

    go(outer=spec1,
       inner=inner,
       outputFile=outputFile,
       mapOptions=mapOptions,
       compareOptions=compareOptions,
       printEventSummary=(not patterns) and (file1 != file2) and 0 <= common["dump"],
       printChannelSummary=file2 and 0 <= common["dump"],
       )


def printHisto(fileName="", histoName=""):
    f = r.TFile(fileName)
    h = f.Get(histoName)
    if not h:
        printer.error("histogram %s not found." % histoName)
        return
    for iBinX in range(0, 2+h.GetNbinsX()):
        w = h.GetBinWidth(iBinX)
        if 1.0e-6 < abs(w - 1.0):
            printer.warning("Histogram %s bin %d has width %g" % (histoName, iBinX, w))

        x = h.GetBinCenter(iBinX)
        c = h.GetBinContent(iBinX)
        stem = histoName.replace("Matched", "")
        if "Ch" in stem:
            stem = stem[:stem.find("Ch")]
        msg = "%3d matched %s: %d events" % (x, stem.ljust(13), c)
        if c:
            if iBinX == 0:
                msg = "<=" + msg
            if iBinX == 1+h.GetNbinsX():
                msg = ">=" + msg
            printer.msg(msg)
    f.Close()
