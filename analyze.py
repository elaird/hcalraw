#! /usr/bin/env python

import os,struct,autoBook,ROOT as r

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
              useEvn = False, filterEvn = False, **_) :
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

def loop(inner = {}, outer = {}, innerEvent = {}, book = {}, payload = True) :
    if inner :
        fI = r.TFile.Open(inner["fileName"])
        treeI = fI.Get(inner["treeName"])

    f = r.TFile.Open(outer["fileName"])
    tree = f.Get(outer["treeName"])

    for iOuterEvent in range(nEvents(tree, outer["nEventsMax"])) :
        nb = tree.GetEntry(iOuterEvent)
        if nb<=0 : continue
        if outer["printRaw"] or (inner and inner["printRaw"]) :
            print "-"*56
        raw = collectedRaw(tree = tree, specs = outer, payload = payload)

        if inner :
            iInnerEvent = innerEvent[iOuterEvent]
            if iInnerEvent==None :continue

            nb = treeI.GetEntry(iInnerEvent)
            if nb<=0 : continue
            rawInner = collectedRaw(tree = treeI, specs = inner, payload = payload)
            compare(raw, rawInner, book = book)
        else :
            compare(raw, book = book)

    f.Close()
    if inner :
        fI.Close()

def collectedRaw(tree = None, specs = {}, payload = True) :
    raw = {}
    for fedId in specs["fedIds"] :
        if specs["format"]=="CMS" :
            rawThisFed = charsOneFed(tree, fedId, specs["rawCollection"])
            raw[fedId] = unpackedHeader(fedData = rawThisFed, bcnDelta = specs["bcnDelta"], chars = True)
            raw[fedId]["nBytesSW"] = rawThisFed.size()
            if payload :
                raw[fedId]["payload"] = unpackedPayload(fedData = rawThisFed, bcnDelta = specs["bcnDelta"], chars = True)
        elif specs["format"]=="HCAL" :
            rawThisFed = wordsOneChunk(tree, fedId)
            raw[fedId] = unpackedHeader(fedData = rawThisFed, bcnDelta = specs["bcnDelta"], chars = False)
            raw[fedId]["nBytesSW"] = rawThisFed.size()*8
            if payload :
                raw[fedId]["payload"] = unpackedPayload(fedData = rawThisFed, bcnDelta = specs["bcnDelta"], chars = False)

    raw[None] = {"print":specs["printRaw"],
                 "label":specs["label"],
                 "bcnDelta":specs["bcnDelta"],
                 "iEntry":tree.GetReadEntry(),
                 }
    return raw

def printRaw(d = {}) :
    aux = d[None]
    print "%4s iEntry 0x%08x (%d)"%(aux["label"], aux["iEntry"], aux["iEntry"])
    print "FEDid     EvN          OrN       BcN   minutes nBytesSW"
    for fedId,data in d.iteritems() :
        if fedId==None : continue
        printRawOneFed(data)
    print

def printRawOneFed(d = {}, htr = True) :
    print "   ".join([" %3d"%d["FEDid"],
                      "0x%07x"%d["EvN"],
                      "0x%08x"%d["OrN"],
                      "%4d"%d["BcN"],
                      "%7.3f"%minutes(d["OrN"]),
                      "%4d"%d["nBytesSW"],
                      ])
    if htr :
        print "uHTR EPCV nWord16"
        for iUhtr in range(12) :
            h = d["uHTR%d"%iUhtr]
            print "%4d %d%d%d%d %7d"%(iUhtr, h["E"], h["P"], h["C"], h["V"], h["nWord16"])

        for offset in sorted(d["payload"].keys()) :
            payload = d["payload"][offset]
            print "%04d"%offset,payload

def bcn(raw, delta = 0) :
    if not delta : return raw
    out = raw + delta
    if out<0    : out += 3564
    if out>3563 : out -= 3564
    return out

def decodeHeader(d = {}, iWord64 = None, word64 = None, bcnDelta = 0) :
    #see http://ohm.bu.edu/~hazen/CMS/SLHC/HcalUpgradeDataFormat_v1_2_2.pdf
    b = [((0xff<<8*i) & word64)>>8*i for i in range(8)]

    if iWord64==0 :
        #d["eight"] = 0xf & b[0]
        #d["fov"] = (0xf0 & b[0])/(1<<4)
        d["FEDid"] = (0xf & b[2])*(1<<8) + b[1]
        d["BcN"] = (0xf0 & b[2])/(1<<4) + b[3]*(1<<4)
        d["EvN"] = b[4] + b[5]*(1<<8) + b[6]*(1<<16)
        d["BcN"] = bcn(d["BcN"], bcnDelta)
        #d["evtTy"] = 0xf & b[7]
        #d["five"] = (0xf0 & b[7])/(1<<4)

    if iWord64==1 :
        #d["zero1"] = 0xf & b[0]
        d["OrN"] = (0xf0 & b[0])/(1<<4) + b[1]*(1<<4) + b[2]*(1<<12) + b[3]*(1<<20) + (0xf & b[4])*(1<<28)

    uhtr = {3:0, 4:4, 5:8}
    if iWord64 in uhtr :
        uhtr0 = uhtr[iWord64]
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

def decodePayload(d = {}, iWord16 = None, word16 = None, bcnDelta = 0) :
    #see http://ohm.bu.edu/~hazen/CMS/SLHC/HcalUpgradeDataFormat_v1_2_2.pdf
    w = word16

    if "iWordZero" not in d :
        d["iWordZero"] = iWord16
        d[d["iWordZero"]] = {}

    l = d[d["iWordZero"]]
    i = iWord16 - d["iWordZero"]
    if i==0 :
        l["InputID"] = (w&0xf0)/(1<<8)
        l["EvN"] = w&0xf
    if i==1 :
        l["EvN"] += w*(1<<8)
    if i==3 :
        l["ModuleId"] = w&0x7ff
        l["OrN"] = (w&0xf800)>>11
    if i==4 :
        l["BcN"] = bcn(w&0xfff, bcnDelta)
        l["FormatVer"] = (w&0xf000)>>12
    if i==5 :
        #l["nWord16"] = w&0x3fff
        l["nWord16"] = 228
    if i<=5 : return

    if i==l["nWord16"]-1 :
        del d["iWordZero"]

def unpacked(fedData = None, iWord64Begin = None, iWord64End = None, chars = None,
             decodeBy64 = None, decode = None, by = None, bcnDelta = 0) :
    assert chars in [False,True],"Specify whether to unpack by words or chars."
    assert decode,"Specify a function to use to interpret the bytes."
    assert by in [16,64],"Specify every how many bits to call decode."
    #see http://ohm.bu.edu/~hazen/CMS/SLHC/HcalUpgradeDataFormat_v1_2_2.pdf
    d = {}
    for iWord64 in range(iWord64Begin, iWord64End) :
        offset = 8*iWord64
        if chars :
            word64 = struct.unpack('Q', "".join([fedData.at(offset+iByte) for iByte in range(8)]))[0]
            #b = [ord(fedData.at(offset+iByte)) for iByte in range(8)] #like above with 'B'*8 rather than 'Q'
        else :
            word64 = fedData.at(iWord64)

        if by==64 :
            decode(d, iWord64, word64, bcnDelta)
        elif by==16 :
            for i in range(4) :
                word16 = (word64&(0xffff<<16*i))>>16*i
                decode(d, 4*iWord64+i, word16, bcnDelta)
    return d

def unpackedPayload(fedData = None, bcnDelta = None, chars = None) :
    nWord64 = fedData.size()/(8 if chars else 1)
    return unpacked(fedData = fedData, bcnDelta = bcnDelta, chars = chars,
                    iWord64Begin = 6, iWord64End = nWord64-1, decode = decodePayload, by = 16)

def unpackedHeader(fedData = None, bcnDelta = None, chars = None) :
    return unpacked(fedData = fedData, bcnDelta = bcnDelta, chars = chars,
                    iWord64Begin = 0, iWord64End = 6, decode = decodeHeader, by = 64)

def unpackedTrailer(fedData = None, bcnDelta = None, chars = None) :
    nWord64 = fedData.size()/(8 if chars else 1)
    return unpacked(fedData = fedData, bcnDelta = bcnDelta, chars = chars,
                    iWord64Begin = nWord64-1, iWord64End = nWord64, decode = decodeTrailer, by = 64)

def charsOneFed(tree = None, fedId = None, collection = "") :
    FEDRawData = getattr(tree, collection).product().FEDData(fedId) #CMS data type
    return r.FEDRawData2(FEDRawData).vectorChar() #wrapper class exposes data_ via data()

def wordsOneChunk(tree = None, fedId = None) :
    chunk = getattr(tree, "Chunk%d"%fedId) #CDF data type
    return r.CDFChunk2(chunk).chunk() #wrapper class creates std::vector<ULong64_t>

def bcnLabel(delta = 0) :
    out = "BcN"
    if delta<0 :
        out += " - %d"%abs(delta)
    elif delta>0 :
        out += " + %d"%abs(delta)
    return out

def compare(raw1 = {}, raw2 = {}, book = {}) :
    if raw1 and raw1[None]["print"] : printRaw(raw1)
    if raw2 and raw2[None]["print"] : printRaw(raw2)

    if raw2 :
        d1 = raw1[989]
        d2 = raw2[700]
        bcnXTitle = "FED 989 %s - FED 700 %s"%(bcnLabel(raw1[None]["bcnDelta"]), bcnLabel(raw2[None]["bcnDelta"]))
        book.fill(d1["OrN"]-d2["OrN"], "deltaOrN", 11, -5.5, 5.5, title = ";FED 989 OrN - FED 700 OrN;Events / bin")
        book.fill(d1["BcN"]-d2["BcN"], "deltaBcN", 11, -5.5, 5.5, title = ";%s;Events / bin"%bcnXTitle)
        book.fill(d1["EvN"]-d2["EvN"], "deltaEvN", 11, -5.5, 5.5, title = ";FED 989 EvN - FED 700 EvN;Events / bin")

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
