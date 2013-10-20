import configuration
import utils


def oneEvent(d={}):
    if None not in d:
        return

    aux = d[None]
    dump = aux["dump"]
    if (not aux["patternMode"]) and (1 <= dump):
        print "-"*86
        print "%4s iEntry 0x%08x (%d)" % (aux["label"],
                                          aux["iEntry"],
                                          aux["iEntry"])

    for fedId, data in d.iteritems():
        if fedId is None:
            continue
        if ("MOL" in data) and (1 <= dump):
            oneFedMol(data["MOL"])
        oneFedHcal(data, patternMode=aux["patternMode"], dump=dump)
    if 1 <= dump:
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


def oneHtrPatterns(p={}, fedId=None, iOffset=None):
    cd = htrChannelData(p["channelData"], p["ModuleId"], fibChs=[1])
    if len(cd) >= 2:
        print "\n".join(patternData(p["patternData"], "%3d %2d" % (fedId, iOffset)))


def oneHtr(p={}, iOffset=None, dump=None):
    out = []
    if (not iOffset) or (4 <= dump):
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

    if 4 <= dump:
        fibChs = [1] if dump == 4 else [0, 1, 2]
        cd = htrChannelData(p["channelData"], p["ModuleId"], fibChs=fibChs)
        if len(cd) >= 2:
            out += cd
    print "\n".join(out)


def qieString(qieData={}):
    l = []
    for iQie in range(12):
        if iQie in qieData:
            l.append("%2x" % qieData[iQie])
        else:
            l.append("  ")
    return " ".join(l)


def htrChannelData(d={}, moduleId=0, fibChs=[]):
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


def patternData(d={}, moduleId=0, slim=True, process=True):
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

            ps = patternString(lst, key, process=process)
            if process and not ps:
                continue

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


def patternString(patterns=[], key="", ascii=True, process=None):
    l = []
    for p in patterns:
        for k in [key+"0", key+"1"]:
            code = p[k]
            if ascii and (32 <= code <= 126):
                l.append("%2s" % chr(code))
            else:
                l.append("%2x" % code)
    out = " ".join(l)

    processed = configuration.processed(out)

    if process:
        if processed:
            return processed
        elif out.replace("0", "").replace(" ", ""):
            return out
        else:
            return ""
    else:
        return out


def oneFedHcal(d={}, patternMode=False, dump=None):
    h = d["header"]
    t = d["trailer"]
    if (not patternMode) and (1 <= dump):
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
        if 2 <= dump:
            htrOverview(h)

    offsets = d["htrBlocks"].keys()
    if not offsets:
        return
    for iOffset, offset in enumerate(sorted(offsets)):
        p = d["htrBlocks"][offset]
        if "patternData" in p:
            oneHtrPatterns(p=p, fedId=d["header"]["FEDid"], iOffset=iOffset)
        elif 3 <= dump:
            oneHtr(p=p, iOffset=iOffset, dump=dump)


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
