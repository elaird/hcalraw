import utils


def oneEvent(d={}, hyphens=True):
    if hyphens:
        print "-"*86

    aux = d[None]
    print "%4s iEntry 0x%08x (%d)" % (aux["label"],
                                      aux["iEntry"],
                                      aux["iEntry"])
    print "   ".join([" FEDid",
                      "  EvN",
                      "       OrN",
                      "    BcN",
                      "minutes",
                      " TTS",
                      " nBytesHW",
                      "nBytesSW",
                     "CRC16",
                      ])
    for fedId, data in d.iteritems():
        if fedId is None:
            continue
        oneFed(data)
    print


def htrOverview(d={}):
    abbr = "uHTR" if "uHTR0" in d else "HTR"
    hyphens = "   "+("-"*(67 if (abbr == "uHTR") else 82))
    print hyphens

    htr = ["  ", "   %4s" % abbr]
    epcv = ["  ", "   EPCV"]
    nWord16 = ["  ", "nWord16"]
    for iHtr in range(15):
        key = "%s%d" % (abbr, iHtr)
        if key not in d:
            continue
        h = d[key]
        htr.append("%4d" % iHtr)
        epcv.append("%d%d%d%d" % (h["E"], h["P"], h["C"], h["V"]))
        nWord16.append("%4d" % (h["nWord16"]))
    for line in [htr, epcv, nWord16]:
        print " ".join(line)
    print hyphens


def htrData(d={}, channelData=True):
    offsets = d["htrBlocks"].keys()
    if offsets:
        for iOffset, offset in enumerate(sorted(offsets)):
            if channelData or not iOffset:
                print "  ".join(["iWord16",
                                 "   EvN",
                                 "  OrN5",
                                 " BcN",
                                 "ModuleId",
                                 "FrmtV",
                                 "nWordTP",
                                 "nWordQIE",
                                 "nSamp",
                                 "nPre",
                                 "EvN8",
                                 "  CRC",
                                 ])
            p = d["htrBlocks"][offset]
            print "  ".join([" %04d" % p["0Word16"],
                             " 0x%07x" % p["EvN"],
                             "0x%02x" % p["OrN5"],
                             "%4d" % p["BcN"],
                             "  0x%03x" % p["ModuleId"],
                             "  0x%01x" % p["FormatVer"],
                             "  %3d  " % p["nWord16Tp"],
                             "   %3d" % p["nWord16Qie"],
                             "    %2d" % p["nSamples"],
                             "  %2d" % p["nPreSamples"],
                             "  0x%02x" % p["EvN8"],
                             "0x%04x" % p["CRC"],
                             ])
            if channelData:
                htrChannelData(p["channelData"], p["ModuleId"])


def qieString(qieData={}):
    l = []
    for iQie in range(12):
        if iQie in qieData:
            l.append("%2x" % qieData[iQie])
        else:
            l.append("  ")
    return " ".join(l)


def htrChannelData(d={}, moduleId=0):
    print "  ".join(["ModuleId",
                     "Fi",
                     "Ch",
                     "Fl",
                     "ErrF",
                     "CapId0",
                     "QIE(hex)  0  1  2  3  4  5  6  7  8  9",
                     ])
    for channelId, data in d.iteritems():
        if channelId % 4 != 1:
            continue
        print "   ".join([" 0x%03x" % moduleId,
                          "%3d" % (channelId/4),
                          "%1d" % (channelId % 4),
                          "%1d" % data["Flavor"],
                          "%2d" % data["ErrF"],
                          "  %1d" % data["CapId0"],
                          " "*11,
                          ])+qieString(data["QIE"])


def oneFed(d={}, overview=True, headers=True, channelData=True):
    print "   ".join(["  %3d" % d["FEDid"],
                      "0x%07x" % d["EvN"],
                      "0x%08x" % d["OrN"],
                      "%4d" % d["BcN"],
                      "%7.3f" % utils.minutes(d["OrN"]),
                      "  %1x" % d["TTS"],
                      "    %4d" % (d["nWord64"]*8),
                      "    %4d" % d["nBytesSW"],
                      " 0x%04x" % d["CRC16"],
                      ])
    if overview:
        htrOverview(d)

    if headers:
        htrData(d, channelData)
