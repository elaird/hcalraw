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

def compare(raw1 = {}, raw2 = {}, book = {}) :
    hyphens = True
    if raw1 and raw1[None]["print"] :
        printRaw(raw1, hyphens)
        hyphens = False
    if raw2 and raw2[None]["print"] :
        printRaw(raw2, hyphens)

    if raw2 :
        d1 = raw1[989]
        d2 = raw2[700]
        bcnXTitle = "FED 989 %s - FED 700 %s"%(bcnLabel(raw1[None]["bcnDelta"]), bcnLabel(raw2[None]["bcnDelta"]))
        book.fill(d1["OrN"]-d2["OrN"], "deltaOrN", 11, -5.5, 5.5, title = ";FED 989 OrN - FED 700 OrN;Events / bin")
        book.fill(d1["BcN"]-d2["BcN"], "deltaBcN", 11, -5.5, 5.5, title = ";%s;Events / bin"%bcnXTitle)
        book.fill(d1["EvN"]-d2["EvN"], "deltaEvN", 11, -5.5, 5.5, title = ";FED 989 EvN - FED 700 EvN;Events / bin")
        book.fill(d1["TTS"], "TTS", 16, -0.5, 15.5, title = ";FED 989 TTS state;Events / bin")

def printRaw(d = {}, hyphens = True) :
    if hyphens :
        print "-"*78

    aux = d[None]
    print "%4s iEntry 0x%08x (%d)"%(aux["label"], aux["iEntry"], aux["iEntry"])
    print " FEDid      EvN          OrN       BcN   minutes     TTS    nBytesHW  nBytesSW   CRC16"
    for fedId,data in d.iteritems() :
        if fedId==None : continue
        printRawOneFed(data)
    print

def printRawOneFed(d = {}, htrOverview = True, htrBlocks = True, channelData = True) :
    print "   ".join(["  %3d"%d["FEDid"],
                      " 0x%07x"%d["EvN"],
                      "0x%08x"%d["OrN"],
                      "%4d"%d["BcN"],
                      "%7.3f"%minutes(d["OrN"]),
                      "   %1x"%d["TTS"],
                      "    %4d"%(d["nWord64"]*8),
                      "   %4d"%d["nBytesSW"],
                      " 0x%04x"%d["CRC16"],
                      ])
    if htrOverview :
        hyphens = "   "+("-"*68)
        print hyphens

        uhtr    = ["  ", "   uHTR"]
        epcv    = ["  ", "   EPCV"]
        nWord16 = ["  ", "nWord16"]
        for iUhtr in range(12) :
            h = d["uHTR%d"%iUhtr]
            uhtr.append("%4d"%iUhtr)
            epcv.append("%d%d%d%d"%(h["E"], h["P"], h["C"], h["V"]))
            nWord16.append("%4d"%(h["nWord16"]))
        for line in [uhtr,epcv,nWord16] :
            print " ".join(line)
        print hyphens

    if htrBlocks :
        offsets = d["htrBlocks"].keys()
        if offsets :
            for iOffset,offset in enumerate(sorted(offsets)) :
                if channelData or not iOffset :
                    print "iWord16     EvN          OrN5      BcN   InputID  ModuleId   nWord16  FormatVer  EvN8     CRC"
                p = d["htrBlocks"][offset]
                print "   ".join([" %04d"%offset,
                                  " 0x%07x"%p["EvN"],
                                  "0x%08x"%p["OrN5"],
                                  "%4d"%p["BcN"],
                                  "  0x%02x"%p["InputID"],
                                  "  0x%03x"%p["ModuleId"],
                                  " %5d"%p["nWord16"],
                                  "    0x%01x"%p["FormatVer"],
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
