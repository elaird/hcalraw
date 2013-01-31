#! /usr/bin/env python

import os,struct,ROOT as r
import autoBook,compare,decode

def setup() :
    assert os.environ["CMSSW_VERSION"],"A CMSSW environment is required (known to work with CMSSW_5_3_7)."

    #batch mode
    r.gROOT.SetBatch(True)

    #silence TCanvas.Print()
    r.gErrorIgnoreLevel = 2000

    #enable convenient use of CMSSW classes
    r.gSystem.Load("libFWCoreFWLite.so")
    r.AutoLibraryLoader.enable()

    #define helper classes
    libs = ["DataFormatsFEDRawData"]
    base = os.environ["CMSSW_RELEASE_BASE"] if os.environ["CMSSW_RELEASE_BASE"] else os.environ["CMSSW_BASE"]
    libPath = "/".join([base, "lib", os.environ["SCRAM_ARCH"]])
    r.gSystem.SetLinkedLibs(" -L"+libPath+" -l".join([""]+libs))
    r.gROOT.LoadMacro("helpers.cxx+")

def nEvents(tree, nMax) :
    nEntries = tree.GetEntries()
    return min(nEntries, nMax) if nMax!=None else nEntries

#this function builds a dictionary, mapping TTree entry to (orn, bcn) or to (orn, bcn, evn)
def eventMaps(fileName = "", treeName = "", format = "", auxBranch = False,
              fedIds = [], bcnDelta = None, rawCollection = None, nEventsMax = None,
              useEvn = False, filterEvn = False, branchName = "", **_) :
    assert fileName
    assert treeName

    forward = {}
    backward = {}
    f = r.TFile.Open(fileName)
    tree = f.Get(treeName)

    for iEvent in range(nEvents(tree, nEventsMax)) :
        orn = bcn = evn = None

        if format=="CMS" :
            if auxBranch and (not useEvn) and (not filterEvn) :
                tree.GetBranch("EventAuxiliary").GetEntry(iEvent)
                orn = tree.EventAuxiliary.orbitNumber()
                bcn = tree.EventAuxiliary.bunchCrossing()
            else :
                tree.GetEntry(iEvent)
                raw = unpacked(fedData = charsOneFed(tree = tree, fedId = fedIds[0], collection = rawCollection),
                               bcnDelta = bcnDelta, chars = True, skipHtrBlocks = True, skipTrailer = True)
                orn = raw["OrN"]
                bcn = raw["BcN"]
                evn = raw["EvN"]

        elif format=="HCAL" :
            if auxBranch and (not useEvn) and (not filterEvn) :
                tree.GetBranch("CDFEventInfo").GetEntry(iEvent)
                orn = tree.CDFEventInfo.getOrbitNumber()
                bcn = tree.CDFEventInfo.getBunchNumber()
            else :
                tree.GetEntry(iEvent)
                raw = unpacked(fedData = wordsOneChunk(tree = tree, fedId = fedIds[0], branchName = branchName),
                               bcnDelta = bcnDelta, chars = False, skipHtrBlocks = True, skipTrailer = True)
                orn = raw["OrN"]
                bcn = raw["BcN"]
                evn = raw["EvN"]

        t = (orn, evn) if useEvn else (orn, )
        if filterEvn and evn&0x1fff :
            continue

        forward[iEvent] = t
        backward[t] = iEvent

    f.Close()
    return forward,backward

def loop(inner = {}, outer = {}, innerEvent = {}, book = {}) :
    if inner :
        fI = r.TFile.Open(inner["fileName"])
        treeI = fI.Get(inner["treeName"])

    f = r.TFile.Open(outer["fileName"])
    tree = f.Get(outer["treeName"])

    for iOuterEvent in range(nEvents(tree, outer["nEventsMax"])) :
        nb = tree.GetEntry(iOuterEvent)
        if nb<=0 : continue

        raw = collectedRaw(tree = tree, specs = outer)

        if inner :
            iInnerEvent = innerEvent[iOuterEvent]
            if iInnerEvent==None :continue

            nb = treeI.GetEntry(iInnerEvent)
            if nb<=0 : continue
            rawInner = collectedRaw(tree = treeI, specs = inner)
            compare.compare(raw, rawInner, book = book)
        else :
            compare.compare(raw, book = book)

    f.Close()
    if inner :
        fI.Close()

def collectedRaw(tree = None, specs = {}) :
    raw = {}
    for fedId in specs["fedIds"] :
        if specs["format"]=="CMS" :
            rawThisFed = charsOneFed(tree, fedId, specs["rawCollection"])
            raw[fedId] = unpacked(fedData = rawThisFed, bcnDelta = specs["bcnDelta"], chars = True, utca = specs["utca"])
            raw[fedId]["nBytesSW"] = rawThisFed.size()
        elif specs["format"]=="HCAL" :
            rawThisFed = wordsOneChunk(tree, fedId, specs["branchName"])
            raw[fedId] = unpacked(fedData = rawThisFed, bcnDelta = specs["bcnDelta"], chars = False, utca = specs["utca"])
            raw[fedId]["nBytesSW"] = rawThisFed.size()*8

    raw[None] = {"print":specs["printRaw"],
                 "label":specs["label"],
                 "bcnDelta":specs["bcnDelta"],
                 "iEntry":tree.GetReadEntry(),
                 }
    return raw

def unpacked(fedData = None, chars = None, skipHtrBlocks = False, skipTrailer = False, bcnDelta = 0, utca = None) :
    assert chars in [False,True],"Specify whether to unpack by words or chars."
    assert skipHtrBlocks or (utca in [False,True]),"Specify whether data is uTCA or VME (unless skipping HTR blocks)."
    #For AMC13, see http://ohm.bu.edu/~hazen/CMS/SLHC/HcalUpgradeDataFormat_v1_2_2.pdf
    #For DCC2, see http://cmsdoc.cern.ch/cms/HCAL/document/CountingHouse/DCC/FormatGuide.pdf
    d = {"htrBlocks":{}}

    nWord64 = fedData.size()/(8 if chars else 1)
    iWordPayload0 = 6 if utca else 12
    iWords = range(nWord64) if not skipHtrBlocks else range(iWordPayload0)+[nWord64-1]
    if skipTrailer : iWords.pop()
    for iWord64 in iWords :
        if chars :
            offset = 8*iWord64
            word64 = struct.unpack('Q', "".join([fedData.at(offset+iByte) for iByte in range(8)]))[0]
            #b = [ord(fedData.at(offset+iByte)) for iByte in range(8)] #like above with 'B'*8 rather than 'Q'
        else :
            word64 = fedData.at(iWord64)

        if iWord64<iWordPayload0 :
            decode.header(d, iWord64, word64, utca, bcnDelta)
        elif iWord64<nWord64-1 :
            for i in range(4) :
                word16 = (word64>>(16*i))&0xffff
                decode.payload(d["htrBlocks"], iWord16 = 4*iWord64+i, word16 = word16,
                               word16Counts = d["word16Counts"], utca = utca, bcnDelta = bcnDelta)
        else :
            if "htrIndex" in d["htrBlocks"] :
                del d["htrBlocks"]["htrIndex"] #fixme
            decode.trailer(d, iWord64, word64, bcnDelta)
    return d

def charsOneFed(tree = None, fedId = None, collection = "") :
    FEDRawData = getattr(tree, collection).product().FEDData(fedId) #CMS data type
    return r.FEDRawData2(FEDRawData).vectorChar() #wrapper class exposes data_ via data()

def wordsOneChunk(tree = None, fedId = None, branchName = "") :
    chunk = getattr(tree, "%s%d"%(branchName, fedId)) #Common Data Format
    return r.CDFChunk2(chunk).chunk() #wrapper class creates std::vector<ULong64_t>

def categories(oMap = {}, iMap = {}, innerEvent = {}) :
    d = {}
    for oEvent,ornEvn in oMap.iteritems() :
        orn = ornEvn[0]
        if oEvent in innerEvent and innerEvent[oEvent]!=None :
            d[orn] = 3
        else :
            d[orn] = 2

    iEvents = innerEvent.values()
    for iEvent,ornEvn in iMap.iteritems() :
        if iEvent in iEvents : continue
        orn = ornEvn[0]
        d[orn] = 1

    return d

def graph(d = {}) :
    gr = r.TGraph()
    for i,key in enumerate(sorted(d.keys())) :
        gr.SetPoint(i, compare.minutes(key), d[key])
    return gr

def eventToEvent(mapF = {}, mapB = {}, useEvn = False, ornTolerance = None) :
    deltaOrnRange = range(-ornTolerance, 1+ornTolerance)
    out = {}
    for oEvent,ornEvn in mapF.iteritems() :
        out[oEvent] = None
        #find match s.t. |orn1 - orn2| < ornRequirement
        orn = ornEvn[0]
        for i in deltaOrnRange :
            ornEvn2 = (orn+i, ornEvn[1]) if useEvn else (orn+i,)
            if ornEvn2 in mapB :
                out[oEvent] = mapB[ornEvn2] #fixme: check for multiple matches
    return out

def go(outer = {}, inner = {}, label = "", useEvn = False, filterEvn = False, ornTolerance = None) :
    innerEvent = {}
    deltaOrn = {}
    oMapF,oMapB = eventMaps(useEvn = useEvn, filterEvn = filterEvn, **outer)
    iMapF = iMapB = {}

    if inner :
        iMapF,iMapB = eventMaps(useEvn = useEvn, filterEvn = filterEvn, **inner)
        innerEvent = eventToEvent(oMapF, iMapB, ornTolerance = ornTolerance)
        if outer["printEventMap"] or inner["printEventMap"] :
            print "oEvent = %s, ornEvn = %s, iEvent = %s"%(str(oEvent),str(ornEvn),str(innerEvent[oEvent]))

    book = autoBook.autoBook("book")
    loop(inner = inner, outer = outer, innerEvent = innerEvent, book = book)

    #write results to a ROOT file
    f = r.TFile("root/%s.root"%label, "RECREATE")
    gr = graph(categories(oMap = oMapF, iMap = iMapF, innerEvent = innerEvent))
    nBoth = len(filter(lambda x:x!=None,innerEvent.values()))

    gr.SetName("category_vs_time")
    labels = ["only %s (%d)"%(inner["label"], len(iMapF)-nBoth) if inner else "",
              "only %s (%d)"%(outer["label"], len(oMapF)-nBoth) if outer else "",
              "both (%d)"%nBoth if inner else "",
              ]
    gr.SetTitle("_".join(labels))
    gr.Write()

    for key,h in book.iteritems() :
        h.Write()
    f.Close()

    s = "%s: %4s = %6d"%(label, outer["label"], len(oMapF))
    if inner :
        s += ", %4s = %6d, both = %6d"%(inner["label"], len(iMapB), len(filter(lambda x:x!=None,innerEvent.values())))
    print s

def oneRun(utcaFileName = "", cmsFileName = "", label = "", useEvn = False, filterEvn = False, ornTolerance = 0, cmsIsLocal = False) :
    utca = {"label":"uTCA",
            "fileName":utcaFileName, "treeName":"CMSRAW", "format":"HCAL", "auxBranch":False,
            "fedIds":[989], "rawCollection": "FEDRawDataCollection_source__demo", "utca":True, "branchName":"Chunk",
            "bcnDelta":-118, "nEventsMax":None,
            "printEventMap":False, "printRaw":True,
            }

    cms = {"label":"CMS",
           "fileName":cmsFileName, "treeName":"Events", "format": "CMS", "auxBranch":True,
           "fedIds":[714,722], "rawCollection":"FEDRawDataCollection_rawDataCollector__LHC", "utca":False,
           "bcnDelta":0, "nEventsMax":None,
           "printEventMap":False, "printRaw":True,
           }
    if cmsIsLocal :
        cms.update({"treeName":"CMSRAW", "format":"HCAL", "auxBranch":False, "branchName":"HCAL_DCC"})

    if utcaFileName :
        if cmsFileName :
            go(outer = utca, inner = cms, label = label, useEvn = useEvn,
               filterEvn = filterEvn, ornTolerance = ornTolerance)
        else :
            go(outer = utca, label = label)
    elif cmsFileName :
        go(outer = cms, label = label)
    else :
        assert False,utcaFileName+" "+cmsFileName

setup()
if __name__=="__main__" :
    #oneRun(utcaFileName = "/afs/cern.ch/user/e/elaird/work/public/d1_utca/usc/USC_209150.root",
    #       cmsFileName  = "/afs/cern.ch/user/e/elaird/work/public/d1_utca/castor/209151.HLTSkim.root",
    #       label = "Run209151",
    #       useEvn = False,
    #       filterEvn = False,
    #       ornTolerance = 0,
    #       )

    oneRun(utcaFileName = "/afs/cern.ch/user/e/elaird/work/public/d1_utca/usc/USC_211155.root",
           cmsFileName = "/afs/cern.ch/user/e/elaird/work/public/d1_utca/usc/USC_211154.root",
           cmsIsLocal = True,
           label = "Run211155",
           useEvn = False,
           filterEvn = False,
           ornTolerance = 0,
           )
