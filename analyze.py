import os
import struct
import utils
r = utils.ROOT()
import autoBook
import compare
import configuration
import decode


def setup():
    r.gROOT.SetBatch(True)
    r.gErrorIgnoreLevel = 2000  # silence TCanvas.Print()
    r.gROOT.LoadMacro("cpp/cdf.cxx+")

    if utils.cmssw():
        #enable convenient use of CMSSW classes
        r.gSystem.Load("libFWCoreFWLite.so")
        r.AutoLibraryLoader.enable()

        #define helper classes
        libs = ["DataFormatsFEDRawData"]
        if os.environ["CMSSW_RELEASE_BASE"]:
            base = os.environ["CMSSW_RELEASE_BASE"]
        else:
            base = os.environ["CMSSW_BASE"]
        libPath = "/".join([base, "lib", os.environ["SCRAM_ARCH"]])
        r.gSystem.SetLinkedLibs(" -L"+libPath+" -l".join([""]+libs))
        r.gROOT.LoadMacro("cpp/cms.cxx+")


setup()


def nEvents(tree, nMax):
    assert tree
    nEntries = tree.GetEntries()
    return min(nEntries, nMax) if (nMax is not None) else nEntries


#this function returns two dictionaries,
#one maps TTree entry to either (orn, ) or to (orn, evn)
#the other maps the reverse
def eventMaps(s={}):
    fileName = s["fileName"]
    treeName = s["treeName"]
    nEventsMax = s["nEventsMax"]
    fedIds = s["fedIds"]
    name = s["name"]
    assert fileName
    assert treeName

    useEvn = configuration.useEvn()
    filterEvn = configuration.filterEvn()
    bcnDelta = configuration.bcnDelta(fedIds[0])
    forward = {}
    backward = {}
    f = r.TFile.Open(fileName)
    if f.IsZombie():
        exit()

    tree = f.Get(treeName)
    if not tree:
        print "tree %s not found.  These objects are available:" % treeName
        f.ls()
        exit()

    for iEvent in range(nEvents(tree, nEventsMax)):
        orn = bcn = evn = None

        if name == "CMS":
            if s["auxBranch"] and (not useEvn) and (not filterEvn):
                tree.GetBranch("EventAuxiliary").GetEntry(iEvent)
                orn = tree.EventAuxiliary.orbitNumber()
                bcn = tree.EventAuxiliary.bunchCrossing()
            else:
                tree.GetEntry(iEvent)
                raw = unpacked(fedData=charsOneFed(tree=tree,
                                                   fedId=fedIds[0],
                                                   collection=s["rawCollection"],
                                                   ),
                               bcnDelta=bcnDelta, chars=True,
                               skipHtrBlocks=True, skipTrailer=True)
                orn = raw["OrN"]
                bcn = raw["BcN"]
                evn = raw["EvN"]

        elif name == "HCAL":
            if s["auxBranch"] and (not useEvn) and (not filterEvn):
                tree.GetBranch("CDFEventInfo").GetEntry(iEvent)
                orn = tree.CDFEventInfo.getOrbitNumber()
                bcn = tree.CDFEventInfo.getBunchNumber()
            else:
                tree.GetEntry(iEvent)
                raw = unpacked(fedData=wordsOneChunk(tree=tree,
                                                     fedId=fedIds[0],
                                                     branchName=s["branch"],
                                                     ),
                               bcnDelta=bcnDelta, chars=False,
                               skipHtrBlocks=True, skipTrailer=True)
                orn = raw["OrN"]
                bcn = raw["BcN"]
                evn = raw["EvN"]

        elif name == "MOL":
            tree.GetEntry(iEvent)
            raw = unpacked(fedData=wordsOneBranch(tree=tree,
                                                  branch=s["branch"],
                                                  ),
                           bcnDelta=bcnDelta, chars=False,
                           skipHtrBlocks=True, skipTrailer=True)
            orn = raw["OrN"]
            bcn = raw["BcN"]
            evn = raw["EvN"]
        else:
            print "ERROR: name %s not found." % name
            exit()

        t = (orn, evn) if useEvn else (orn, )
        if filterEvn and (evn & 0x1fff):
            continue

        forward[iEvent] = t
        backward[t] = iEvent

    f.Close()
    return forward, backward


def loop(inner={}, outer={}, innerEvent={}, book={}):
    if inner:
        fI = r.TFile.Open(inner["fileName"])
        treeI = fI.Get(inner["treeName"])
        assert treeI, inner["treeName"]

    f = r.TFile.Open(outer["fileName"])
    tree = f.Get(outer["treeName"])
    assert tree, outer["treeName"]

    for iOuterEvent in range(nEvents(tree, outer["nEventsMax"])):
        nb = tree.GetEntry(iOuterEvent)
        if nb <= 0:
            continue

        raw = collectedRaw(tree=tree, specs=outer)

        if inner:
            iInnerEvent = innerEvent[iOuterEvent]
            if iInnerEvent is None:
                continue

            nb = treeI.GetEntry(iInnerEvent)
            if nb <= 0:
                continue

            rawInner = collectedRaw(tree=treeI, specs=inner)
            compare.compare(raw, rawInner, book=book)
        else:
            compare.compare(raw, book=book)

    f.Close()
    if inner:
        fI.Close()


def collectedRaw(tree=None, specs={}):
    raw = {}
    for fedId in specs["fedIds"]:
        if specs["name"] == "CMS":
            rawThisFed = charsOneFed(tree, fedId, specs["rawCollection"])
            raw[fedId] = unpacked(fedData=rawThisFed,
                                  bcnDelta=configuration.bcnDelta(fedId),
                                  chars=True,
                                  utca=not configuration.isVme(fedId),
                                  skipFlavors=configuration.unpackSkipFlavors(fedId),
                                  patternMode=specs["patternMode"],
                                  )
            raw[fedId]["nBytesSW"] = rawThisFed.size()
        elif specs["name"] == "HCAL":
            rawThisFed = wordsOneChunk(tree, fedId, specs["branch"])
            raw[fedId] = unpacked(fedData=rawThisFed,
                                  bcnDelta=configuration.bcnDelta(fedId),
                                  chars=False,
                                  utca=not configuration.isVme(fedId),
                                  skipFlavors=configuration.unpackSkipFlavors(fedId),
                                  patternMode=specs["patternMode"],
                                  )
            raw[fedId]["nBytesSW"] = rawThisFed.size()*8
        elif specs["name"] == "MOL":
            rawThisFed = wordsOneBranch(tree=tree, branch=specs["branch"])
            raw[fedId] = MOLunpacked(fedData=rawThisFed,
                                  bcnDelta=configuration.bcnDelta(fedId),
                                  chars=False,
                                  utca=not configuration.isVme(fedId),
                                  skipFlavors=configuration.unpackSkipFlavors(fedId),
                                  patternMode=specs["patternMode"],
                                  )
            raw[fedId]["nBytesSW"] = rawThisFed.size()*8
    raw[None] = {"iEntry": tree.GetReadEntry(),
                 "label": specs["label"],
                 "patternMode": specs["patternMode"],
                 }
    return raw


#AMC13 http://ohm.bu.edu/~hazen/CMS/SLHC/HcalUpgradeDataFormat_v1_2_2.pdf
#DCC2 http://cmsdoc.cern.ch/cms/HCAL/document/CountingHouse/DCC/FormatGuide.pdf
def unpacked(fedData=None, chars=None, skipHtrBlocks=False, skipTrailer=False,
             skipWords64=[], bcnDelta=0, utca=None, skipFlavors=[], patternMode=False):
    assert chars in [False, True], \
        "Specify whether to unpack by words or chars."
    assert skipHtrBlocks or (utca in [False, True]), \
        "Specify whether data is uTCA or VME (unless skipping HTR blocks)."
    header = {}
    trailer = {}
    htrBlocks = {}

    nWord64 = fedData.size()/(8 if chars else 1)
    iWordPayload0 = 6 if utca else 12

    if skipHtrBlocks:
        iWords = range(iWordPayload0)+[nWord64-1]
    else:
        iWords = range(nWord64)
    if skipTrailer:
        iWords.pop()

    nToSkip = len(set(skipWords64))
    nSkipped64 = 0
    for jWord64 in iWords:
        if chars:
            offset = 8*jWord64
            bytes = [fedData.at(offset+iByte) for iByte in range(8)]
            word64 = struct.unpack('Q', "".join(bytes))[0]
            #like above with 'B'*8 rather than 'Q':
            #b = [ord(fedData.at(offset+iByte)) for iByte in range(8)]
        else:
            word64 = fedData.at(jWord64)

        if jWord64 in skipWords64:
            nSkipped64 += 1
            continue
        iWord64 = jWord64 - nSkipped64

        if iWord64 < iWordPayload0:
            decode.header(header, iWord64, word64, utca, bcnDelta)
        elif iWord64 < nWord64 - 1 - nToSkip: 
            for i in range(4):
                word16 = (word64 >> (16*i)) & 0xffff
                iWord16 = 4*iWord64+i
                returnCode = decode.payload(htrBlocks,
                                            iWord16=iWord16, word16=word16,
                                            word16Counts=header["word16Counts"],
                                            utca=utca, bcnDelta=bcnDelta,
                                            skipFlavors=skipFlavors,
                                            patternMode=patternMode)
                if returnCode is not None:
                    print " ".join(["WARNING: skipping",
                                    "FED %d" % header["FEDid"],
                                    "event %d" % header["EvN"],
                                    "iWord16 %d" % iWord16,
                                    ])
        else:
            if "htrIndex" in htrBlocks:
                del htrBlocks["htrIndex"]  # fixme
            decode.trailer(trailer, iWord64, word64)

    # fixme: improve this
    out = {}
    out.update(header)
    out.update(trailer)
    out.update({"htrBlocks": htrBlocks})
    return out

#FEROL https://twiki.cern.ch/twiki/bin/viewauth/CMS/CMD_FEROL_DOC
def MOLunpacked(fedData=None, chars=None, skipHtrBlocks=False, skipTrailer=False,
             bcnDelta=0, utca=None, skipFlavors=[], patternMode=False):
    MOLheader = {}
    out = {}

    BlockHeaderList = [] #List for storing block headers
    
    for iWord64 in range(fedData.size()-1):
        word64 = fedData.at(iWord64)

        #If it's a new block, the first two lines are the blockheaders
        if word64 & 0xffff ==  0x5A47: 
            decode.MOLheader(MOLheader, utils.Swap64(word64), utils.Swap64(fedData.at(iWord64+1))) #endian flip for block headers
            BlockHeaderList.append(iWord64)
            BlockHeaderList.append(iWord64+1)
            out.update(MOLheader)  
          
    #Load Sub-detector Payload with unpacked()
    outUnpacked = {}
    outUnpacked = unpacked(fedData=fedData, chars=chars, skipHtrBlocks=skipHtrBlocks, 
                           skipTrailer=skipTrailer, skipWords64=BlockHeaderList, 
                           bcnDelta=bcnDelta, utca=utca, skipFlavors=skipFlavors, 
                           patternMode=patternMode)
    out.update(outUnpacked)
    return out

def charsOneFed(tree=None, fedId=None, collection=""):
    #CMS data type
    FEDRawData = getattr(tree, collection).product().FEDData(fedId)
    #wrapper class exposes data_ via data()
    return r.FEDRawData2(FEDRawData).vectorChar()


def wordsOneChunk(tree=None, fedId=None, branchName=""):
    #Common Data Format
    chunk = wordsOneBranch(tree, "%s%d" % (branchName, fedId))
    #wrapper class creates std::vector<ULong64_t>
    return r.CDFChunk2(chunk).chunk()


def wordsOneBranch(tree=None, branch=""):
    try:
        chunk = getattr(tree, branch)
    except AttributeError:
        print "Branch %s not found.  These branches are available:" % branch
        names = [item.GetName() for item in tree.GetListOfBranches()]
        for name in sorted(names):
            print name
        exit()
    return chunk


def categories(oMap={}, iMap={}, innerEvent={}):
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
    for i, key in enumerate(sorted(d.keys())):
        gr.SetPoint(i, utils.minutes(key), d[key])
    return gr


def eventToEvent(mapF={}, mapB={}):
    useEvn = configuration.useEvn()
    ornTolerance = configuration.ornTolerance()

    deltaOrnRange = range(-ornTolerance, 1+ornTolerance)
    out = {}
    for oEvent, ornEvn in mapF.iteritems():
        out[oEvent] = None
        #find match s.t. |orn1 - orn2| <= ornTolerance
        orn = ornEvn[0]
        for i in deltaOrnRange:
            ornEvn2 = (orn+i, ornEvn[1]) if useEvn else (orn+i,)
            if ornEvn2 in mapB:
                #fixme: check for multiple matches
                out[oEvent] = mapB[ornEvn2]
    return out


def go(outer={}, inner={}, label="", patternMode=None):
    innerEvent = {}
    deltaOrn = {}

    oMapF, oMapB = eventMaps(outer)
    iMapF = iMapB = {}

    if inner:
        iMapF, iMapB = eventMaps(inner)
        innerEvent = eventToEvent(oMapF, iMapB)
        if configuration.identityMap():
            for key in innerEvent.keys():
                innerEvent[key] = key
        if configuration.printEventMap():
            for oEvent, iEvent in sorted(innerEvent.iteritems()):
                print ", ".join(["oEvent = %s" % str(oEvent),
                                 "oOrnEvn = %s" % str(oMapF[oEvent]),
                                 "iEvent = %s" % str(iEvent),
                                 ])

    book = autoBook.autoBook("book")
    loop(inner=inner, outer=outer, innerEvent=innerEvent, book=book)

    #write results to a ROOT file
    f = r.TFile("%s/%s.root" % (utils.outputDir(), label), "RECREATE")
    gr = graph(categories(oMap=oMapF, iMap=iMapF, innerEvent=innerEvent))
    nBoth = len(filter(lambda x: x is not None, innerEvent.values()))

    gr.SetName("category_vs_time")
    labels = ["only %s (%d)" % (inner["label"],
                                len(iMapF)-nBoth) if inner else "",
              "only %s (%d)" % (outer["label"],
                                len(oMapF)-nBoth) if outer else "",
              "both (%d)" % nBoth if inner else "",
              ]
    gr.SetTitle("_".join(labels))
    gr.Write()

    for key, h in book.iteritems():
        h.Write()
    f.Close()

    if not patternMode:
        s = "%s: %4s = %6d" % (label, outer["label"], len(oMapF))
        if inner:
            s += ", %4s = %6d, both = %6d" % (inner["label"], len(iMapB), nBoth)
        print s


def fileSpec(fileName="", someFedId=None):
    f = r.TFile(fileName)
    if f.IsZombie():
        exit()
    treeNames = []
    for tkey in f.GetListOfKeys():
        obj = f.Get(tkey.GetName())
        if obj.ClassName() == "TTree":
            treeNames.append(obj.GetName())

    specs = []
    for treeName in set(treeNames):  # set accomodate cycles, e.g. CMSRAW;3 CMSRAW;4
        spec = configuration.format(treeName, someFedId)
        if spec:
            specs.append(spec)

    if len(specs) != 1:
        print "ERROR: found multiple known TTrees in file %s" % fileName
        print specs
        exit()
    else:
        return specs[0]
    f.Close()


def oneRun(file1="",
           feds1=[],
           file2="",
           feds2=[],
           patternMode=None,
           nEvents=None,
           label="",
           ):

    assert file1
    assert feds1
    spec1 = fileSpec(file1, feds1[0])
    spec1.update({"fileName": file1,
                  "fedIds": feds1,
                  "nEventsMax": nEvents,
                  "patternMode": patternMode,
                  "label": "file1",
                  })

    if file2:
        assert feds2
        spec2 = fileSpec(file2, feds2[0])
        spec2.update({"fileName": file2,
                      "fedIds": feds2,
                      "nEventsMax": nEvents,
                      "patternMode": patternMode,
                      "label": "file2",
                      })
        go(outer=spec1, inner=spec2, label=label, patternMode=patternMode)
    else:
        go(outer=spec1, label=label, patternMode=patternMode)


def printHisto(label="", histoName="MatchedFibers"):
    f = r.TFile("%s/%s.root" % (utils.outputDir(), label))
    h = f.Get(histoName)
    if not h:
        print "ERROR: histogram %s not found." % histoName
        return
    for iBinX in range(0, 2+h.GetNbinsX()):
        x = h.GetBinCenter(iBinX)
        c = h.GetBinContent(iBinX)
        msg = "%d matched fibers: %d events" % (x, c)
        if c:
            if iBinX == 0:
                msg = "<=" + msg
            if iBinX == 1+h.GetNbinsX():
                msg = ">=" + msg
            print msg
    f.Close()
