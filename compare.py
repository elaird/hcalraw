def minutes(orn) :
    orbPerSec = 11.1e3
    return orn/orbPerSec/60.0

def bcnLabel(delta = 0) :
    out = "BcN"
    if delta<0 :
        out += " - %d"%abs(delta)
    elif delta>0 :
        out += " + %d"%abs(delta)
    return out

def singleFedPlots(raw = {}, fedId = None, book = {}) :
    d = raw[fedId]
    book.fill(d["TTS"], "TTS_%d"%fedId, 16, -0.5, 15.5, title = "FED %d; TTS state;Events / bin"%fedId)

    caps = {0:0, 1:0, 2:0, 3:0}
    ErrF = {0:0, 1:0, 2:0, 3:0}
    for block in d["htrBlocks"].values() :
        for channelId,channelData in block["channelData"].iteritems() :
            ErrF[channelData["ErrF"]] += 1
            if not channelData["ErrF"] :
                caps[channelData["CapId0"]] += 1
    book.fill(ErrF[0]/(0.0+sum(ErrF.values())), "ErrF0_%d"%fedId, 44, 0.0, 1.1, title = "FED %d;frac. chan. w/ErrF==0"%fedId)
    book.fill(max(caps.values())/(0.0+sum(caps.values())), "PopCapFrac_%d"%fedId, 44, 0.0, 1.1,
              title = "FED %d;frac. ErrF=0 chans w/most pop. capId"%fedId)

def compare(raw1 = {}, raw2 = {}, book = {}) :
    hyphens = True
    if raw1 and raw1[None]["print"] :
        printRaw(raw1, hyphens)
        hyphens = False
    if raw2 and raw2[None]["print"] :
        printRaw(raw2, hyphens)

    if raw1 :
        d1 = raw1[989]
        singleFedPlots(raw1, 989, book)

    if raw2 :
        d2 = raw2[700]
        singleFedPlots(raw2, 700, book)

    if raw1 and raw2 :
        bcnXTitle = "FED 989 %s - FED 700 %s"%(bcnLabel(raw1[None]["bcnDelta"]), bcnLabel(raw2[None]["bcnDelta"]))
        book.fill(d1["OrN"]-d2["OrN"], "deltaOrN", 11, -5.5, 5.5, title = ";FED 989 OrN - FED 700 OrN;Events / bin")
        book.fill(d1["BcN"]-d2["BcN"], "deltaBcN", 11, -5.5, 5.5, title = ";%s;Events / bin"%bcnXTitle)
        book.fill(d1["EvN"]-d2["EvN"], "deltaEvN", 11, -5.5, 5.5, title = ";FED 989 EvN - FED 700 EvN;Events / bin")

def printRaw(d = {}, hyphens = True) :
    if hyphens :
        print "-"*86

    aux = d[None]
    print "%4s iEntry 0x%08x (%d)"%(aux["label"], aux["iEntry"], aux["iEntry"])
    print " FEDid     EvN          OrN       BcN   minutes    TTS    nBytesHW  nBytesSW   CRC16"
    for fedId,data in d.iteritems() :
        if fedId==None : continue
        printRawOneFed(data)
    print

def printRawOneFed(d = {}, htrOverview = True, htrHeaders = True, channelData = True) :
    print "   ".join(["  %3d"%d["FEDid"],
                      "0x%07x"%d["EvN"],
                      "0x%08x"%d["OrN"],
                      "%4d"%d["BcN"],
                      "%7.3f"%minutes(d["OrN"]),
                      "  %1x"%d["TTS"],
                      "    %4d"%(d["nWord64"]*8),
                      "   %4d"%d["nBytesSW"],
                      " 0x%04x"%d["CRC16"],
                      ])
    if htrOverview :
        abbr = "uHTR" if "uHTR0" in d else "HTR"
        hyphens = "   "+("-"*(67 if abbr=="uHTR" else 82))
        print hyphens

        htr     = ["  ", "   %4s"%abbr]
        epcv    = ["  ", "   EPCV"]
        nWord16 = ["  ", "nWord16"]
        for iHtr in range(15) :
            key = "%s%d"%(abbr,iHtr)
            if key not in d : continue
            h = d[key]
            htr.append("%4d"%iHtr)
            epcv.append("%d%d%d%d"%(h["E"], h["P"], h["C"], h["V"]))
            nWord16.append("%4d"%(h["nWord16"]))
        for line in [htr,epcv,nWord16] :
            print " ".join(line)
        print hyphens

    if htrHeaders :
        offsets = d["htrBlocks"].keys()
        if offsets :
            for iOffset,offset in enumerate(sorted(offsets)) :
                if channelData or not iOffset :
                    print "iWord16     EvN    OrN5   BcN  InpID  ModuleId  FrmtV  "+\
                          "nWordTP  nWordQIE  nSamp  nPre  EvN8    CRC"
                p = d["htrBlocks"][offset]
                print "  ".join([" %04d"%p["0Word16"],
                                 " 0x%07x"%p["EvN"],
                                 "0x%02x"%p["OrN5"],
                                 "%4d"%p["BcN"],
                                 " 0x%02x"%p["InputID"],
                                 "  0x%03x"%p["ModuleId"],
                                 "  0x%01x"%p["FormatVer"],
                                 "  %3d  "%p["nWord16Tp"],
                                 "   %3d"%p["nWord16Qie"],
                                 "    %2d"%p["nSamples"],
                                 "  %2d"%p["nPreSamples"],
                                 "  0x%02x"%p["EvN8"],
                                 "0x%04x"%p["CRC"],
                                 ])
                if channelData :
                    print "ModuleId  Ch  Fl  ErrF CapId0  QIE(hex)  0  1  2  3  4  5  6  7  8  9"
                    for channelId,data in p["channelData"].iteritems() :
                        print "   ".join([" 0x%03x"%p["ModuleId"],
                                          "%3d"%channelId,
                                          "%1d"%data["Flavor"],
                                          "%2d"%data["ErrF"],
                                          "  %1d"%data["CapId0"],
                                          " "*10,
                                          ])+\
                                          " ".join(["%2x"%data["QIE"][iQie] if iQie in data["QIE"] else "  " \
                                                    for iQie in range(12)])
