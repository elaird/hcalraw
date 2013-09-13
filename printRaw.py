import configuration
import utils


def oneEvent(d={}):
    if not all([d, configuration.printFibCh()]):
        return

    aux = d[None]
    if not aux["patternMode"]:
        print "-"*86
        print "%4s iEntry 0x%08x (%d)" % (aux["label"],
                                          aux["iEntry"],
                                          aux["iEntry"])

    for fedId, data in d.iteritems():
        if fedId is None:
            continue
        if "MOL" in data:
            oneFedMol(data["MOL"])
        oneFedHcal(data, skipFed=aux["patternMode"]);
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
            p = d["htrBlocks"][offset]
            patterns = "patternData" in p
            out = []
            if not patterns:
                if channelData or not iOffset:
                    out.append("  ".join(["iWord16",
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
                                          ]))

                out.append("  ".join([" %04d" % p["0Word16"],
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
                                      ]))
            if channelData or patterns:
                cd = htrChannelData(p["channelData"], p["ModuleId"])
            if channelData and not patterns:
                out += cd
            if patterns and len(cd) > 1:
                out += patternData(p["patternData"], "%3d %2d" % (d["header"]["FEDid"], iOffset))
            if len(out) >= 4:
                print "\n".join(out)


def qieString(qieData={}):
    l = []
    for iQie in range(12):
        if iQie in qieData:
            l.append("%2x" % qieData[iQie])
        else:
            l.append("  ")
    return " ".join(l)


def htrChannelData(d={}, moduleId=0):
    out = []
    out.append("  ".join(["ModuleId",
                          "Fi",
                          "Ch",
                          "Fl",
                          "ErrF",
                          "CapId0",
                          "QIE(hex)  0  1  2  3  4  5  6  7  8  9",
                          ])
               )
    fibChs = configuration.printFibCh()
    skipErrF = configuration.printSkipErrF()
    for channelId, data in d.iteritems():
        if data["FibCh"] not in fibChs:
            continue
        if data["ErrF"] in skipErrF:
            continue
        out.append("   ".join([" 0x%03x" % moduleId,
                               "%3d" % data["Fiber"],
                               "%1d" % data["FibCh"],
                               "%1d" % data["Flavor"],
                               "%2d" % data["ErrF"],
                               "  %1d" % data["CapId0"],
                               " "*11,
                               ])+qieString(data["QIE"])
                   )
    return out


def patternData(d={}, moduleId=0, slim=True):
    if slim:
        out = [""]
    else:
        headers = ["ModuleId", "Fibers", "Pattern"]
        chars = " ".join(["%2d" % i for i in range(20)])
        out = ["  ".join(headers+[chars])]

    for fiber1, lst in d.iteritems():
        for key in ["A", "B", "C"]:
            if slim and key == "B":
                continue

            ps = patternString(lst, key)
            if key == "B":
                fibers = "  %2d,%2d" % (fiber1, 1+fiber1)
            elif key == "A":
                fibers = "     %2d" % (fiber1)
            elif key == "C":
                fibers = "     %2d" % (1 + fiber1)

            if slim:
                out.append("%s %2d:  %s" % (moduleId, 1 + int(fibers), ps))
            else:
                out.append("   ".join([moduleId, fibers, "  %s" % key, "  "]) + ps)
    return out


def patternString(patterns=[], key="", ascii=True):
    l = []
    for p in patterns:
        for k in [key+"0", key+"1"]:
            code = p[k]
            if ascii and (32 <= code <= 126):
                l.append("%2s" % chr(code))
            else:
                l.append("%2x" % code)
    return " ".join(l)


def oneFedHcal(d={}, overview=True, headers=True, channelData=True, skipFed=False):
    h = d["header"]
    t = d["trailer"]
    if not skipFed:
        print "-"*85
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

        print "   ".join(["  %3d" % h["FEDid"],
                          "0x%07x" % h["EvN"],
                          "0x%08x" % h["OrN"],
                          "%4d" % h["BcN"],
                          "%7.3f" % utils.minutes(h["OrN"]),
                          ("  %1x" % t["TTS"]) if "TTS" in t else "  - ",
                          ("    %4d" % (t["nWord64"]*8)) if "nWord64" in t else "    --  ",
                          "    %4d" % d["nBytesSW"],
                          (" 0x%04x" % t["CRC16"]) if "CRC16" in t else "   - ",
                          ])
        if overview:
            htrOverview(h)

    if headers:
        htrData(d, channelData=channelData)


def oneFedMol(d):
    print "--MOL"+("-"*34)
    print "   ".join([" FEDid  ",
                      "EvN ",
                      "   iBlock",
                      "  nWord64",
                      ])

    for iBlock in sorted(d.keys()):
        value = d[iBlock]
        print "   ".join(["  %3d" % value["FEDid"],
                          "0x%07x" % value["Trigger"],
                          "%5d" % iBlock,
                          "    %5d" % value["nWord64"]])
