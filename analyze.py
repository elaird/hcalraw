#! /usr/bin/env python

import os,struct,autoBook,ROOT as r

def setup() :
    assert os.environ["CMSSW_VERSION"],"A CMSSW environment is required (known to work with CMSSW_5_3_4)."

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
              useEvn = False, filterEvn = False, **_) :
    assert fileName
    assert treeName

    forward = {}
    backward = {}
    f = r.TFile(fileName)
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
                raw = unpackedHeader(fedData = charsOneFed(tree = tree, fedId = fedIds[0], collection = rawCollection),
                                     bcnDelta = bcnDelta, chars = True)
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
                raw = unpackedHeader(fedData = wordsOneChunk(tree = tree, fedId = fedIds[0]),
                                     bcnDelta = bcnDelta, chars = False)
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
        fI = r.TFile(inner["fileName"])
        treeI = fI.Get(inner["treeName"])

    f = r.TFile(outer["fileName"])
    tree = f.Get(outer["treeName"])

    for iOuterEvent in range(nEvents(tree, outer["nEventsMax"])) :
        nb = tree.GetEntry(iOuterEvent)
        if nb<=0 : continue
        if outer["printRaw"] or (inner and inner["printRaw"]) :
            print "-"*56
        raw = collectedRaw(tree = tree, specs = outer)

        if inner :
            iInnerEvent = innerEvent[iOuterEvent]
            if iInnerEvent==None :continue

            nb = treeI.GetEntry(iInnerEvent)
            if nb<=0 : continue
            rawInner = collectedRaw(tree = treeI, specs = inner)
            compare(raw, rawInner, book = book)
        else :
            compare(raw, book = book)

    f.Close()
    if inner :
        fI.Close()

def collectedRaw(tree = None, specs = {}) :
    raw = {}
    for fedId in specs["fedIds"] :
        if specs["format"]=="CMS" :
            rawThisFed = charsOneFed(tree, fedId, specs["rawCollection"])
            raw[fedId] = unpackedHeader(fedData = rawThisFed, bcnDelta = specs["bcnDelta"], chars = True)
            size = rawThisFed.size()
        elif specs["format"]=="HCAL" :
            rawThisFed = wordsOneChunk(tree, fedId)
            raw[fedId] = unpackedHeader(fedData = rawThisFed, bcnDelta = specs["bcnDelta"], chars = False)
            size = rawThisFed.size()*8

    if specs["printRaw"] :
        iEvent = tree.GetReadEntry()
        print "%4s iEvent 0x%08x (%d)"%(specs["label"], iEvent, iEvent)
        print "FEDid     EvN          OrN       BcN   minutes nBytesSW"
        for fedId,data in raw.iteritems() :
            printRaw(data, aux = {"fedId":fedId, "size":size})
        print
    return raw

def printRaw(d = {}, aux = {}, htr = False) :
    m = minutes(d["OrN"], d["BcN"])
    print "   ".join([" %3d"%d["FEDid"],
                      "0x%07x"%d["EvN"],
                      "0x%08x"%d["OrN"],
                      "%4d"%d["BcN"],
                      "%7.3f"%m,
                      "%4d"%aux["size"],
                      ])
    if htr :
        print "uHTR EPCV nWord16"
        for iUhtr in range(12) :
            h = d["uHTR%d"%iUhtr]
            print "%4d %d%d%d%d %7d"%(iUhtr, h["E"], h["P"], h["C"], h["V"], h["nWord16"])

def decodedHeader(d = {}, offset = None, bytes = None, bcnDelta = 0) :
    #see http://ohm.bu.edu/~hazen/CMS/SLHC/HcalUpgradeDataFormat_v1_2_2.pdf
    b = bytes
    if offset==0x00 :
        #d["eight"] = 0xf & b[0]
        #d["fov"] = (0xf0 & b[0])/(1<<4)
        d["FEDid"] = (0xf & b[2])*(1<<8) + b[1]
        d["BcN"] = (0xf0 & b[2])/(1<<4) + b[3]*(1<<4)
        d["EvN"] = b[4] + b[5]*(1<<8) + b[6]*(1<<16)
        #d["evtTy"] = 0xf & b[7]
        #d["five"] = (0xf0 & b[7])/(1<<4)

        if bcnDelta :
            bcn = d["BcN"]+bcnDelta
            if bcn<0    : bcn += 3564
            if bcn>3563 : bcn -= 3564
            d["BcN"] = bcn

    if offset==0x08 :
        #d["zero1"] = 0xf & b[0]
        d["OrN"] = (0xf0 & b[0])/(1<<4) + b[1]*(1<<4) + b[2]*(1<<12) + b[3]*(1<<20) + (0xf & b[4])*(1<<28)

    uhtr = {0x18:0,
            0x20:4,
            0x28:8,
            }
    if offset in uhtr :
        uhtr0 = uhtr[offset]
        for i in range(4) :
            key = "uHTR%d"%(uhtr0+i)
            b0 = b[  2*i]
            b1 = b[1+2*i]
            d[key] = {"E":(b1&80)>>6,
                      "P":(b1&40)>>5,
                      "C":(b1&20)>>4,
                      "V":(b1&10)>>3,
                      "nWord16":(b1 & 0xf)*(1<<4) + b0,
                      }
    return d

def unpacked(fedData = None, iWord64Begin = None, iWord64End = None, chars = None, decode = None, bcnDelta = 0) :
    assert chars in [False,True],"Specify whether to unpack by words or chars."
    assert decode,"Specify a function to use to interpret the bytes."

    #see http://ohm.bu.edu/~hazen/CMS/SLHC/HcalUpgradeDataFormat_v1_2_2.pdf
    d = {}
    fmt = 'B'*8
    bytes = range(8)
    for iWord64 in range(iWord64Begin, iWord64End) :
        offset = 8*iWord64
        if chars :
            b = struct.unpack(fmt, "".join([fedData.at(offset+iByte) for iByte in bytes]))
            #b = [ord(fedData.at(offset+iByte)) for iByte in range(8)] #same result as above line
        else :
            w = fedData.at(iWord64)
            b = [((0xff<<8*i) & w)>>8*i for i in bytes]
        decode(d, offset, b, bcnDelta)
    return d

def unpackedPayload(fedData = None, bcnDelta = None, chars = None) :
    nWord64 = fedData.size()/(8 if chars else 1)
    return unpacked(fedData = fedData, bcnDelta = bcnDelta, chars = chars,
                    iWord64Begin = 6, iWord64End = nWord64)

def unpackedHeader(fedData = None, bcnDelta = None, chars = None) :
    return unpacked(fedData = fedData, bcnDelta = bcnDelta, chars = chars,
                    iWord64Begin = 0, iWord64End = 6, decode = decodedHeader)

def charsOneFed(tree = None, fedId = None, collection = "") :
    FEDRawData = getattr(tree, collection).product().FEDData(fedId) #CMS data type
    return r.FEDRawData2(FEDRawData).vectorChar() #wrapper class exposes data_ via data()

def wordsOneChunk(tree = None, fedId = None) :
    chunk = getattr(tree, "Chunk%d"%fedId) #CDF data type
    return r.CDFChunk2(chunk).chunk() #wrapper class creates std::vector<ULong64_t>

def compare(raw1 = {}, raw2 = {}, book = {}) :
    d1 = raw1[989]
    d2 = raw2[700]
    book.fill(d1["OrN"]-d2["OrN"], "deltaOrn", 11, -5.5, 5.5)
    book.fill(d1["BcN"]-d2["BcN"], "deltaBcN", 2*3564+1, -3564.5, 3564.5)

def minutes(orn) :
    orbPerSec = 11.1e3
    return orn/orbPerSec/60.0

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
        gr.SetPoint(i, minutes(key), d[key])
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
    gr.SetTitle("only %s (%d)_only %s (%d)_%s (%d)"%(inner["label"], len(iMapF)-nBoth,
                                                     outer["label"], len(oMapF)-nBoth,
                                                     "both", nBoth))
    gr.Write()
    for key,h in book.iteritems() :
        h.Write()
    f.Close()

    s = "%s: %4s = %6d"%(label, outer["label"], len(oMapF))
    if inner :
        s += ", %4s = %6d, both = %6d"%(inner["label"], len(iMapB), len(filter(lambda x:x!=None,innerEvent.values())))
    print s

def oneRun(utcaFileName = "", cmsFileName = "", label = "", useEvn = False, filterEvn = False, ornTolerance = 0) :
    utca = {"label":"uTCA",
            "fileName":utcaFileName, "treeName":"CMSRAW", "format":"HCAL", "auxBranch":False,
            "fedIds":[989], "rawCollection": "FEDRawDataCollection_source__demo",
            "bcnDelta":-118, "nEventsMax":None,
            "printEventMap":False, "printRaw":False,
            }

    cms = {"label":"CMS",
           "fileName":cmsFileName, "treeName":"Events", "format": "CMS", "auxBranch":True,
           "fedIds":range(700,702), "rawCollection":"FEDRawDataCollection_rawDataCollector__LHC",

           "bcnDelta":0, "nEventsMax":None,
           "printEventMap":False, "printRaw":False,
           }

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
    oneRun(utcaFileName = "/afs/cern.ch/user/e/elaird/work/public/d1_utca/usc/USC_209150.root",
           cmsFileName  = "/afs/cern.ch/user/e/elaird/work/public/d1_utca/castor/209151.HLTSkim.root",
           label = "Run209151",
           useEvn = False,
           filterEvn = False,
           ornTolerance = 0,
           )
