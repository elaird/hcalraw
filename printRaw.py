import configuration
import printer
import utils


def reduced(lst=[], value=None):
    subList = filter(lambda x: x[0] == value, lst)
    return map(lambda x: x[1:], subList)


def oneEvent(d={}, nonMatched=[]):
    if None not in d:
        return

    aux = d[None]
    dump = aux["dump"]
    if (not aux["patternMode"]) and (1 <= dump):
        printer.purple("-"*85)
        printer.purple("%4s iEntry 0x%08x (%d)" % (aux["label"],
                                                   aux["iEntry"],
                                                   aux["iEntry"]))

    for fedId, data in d.iteritems():
        if fedId is None:
            continue
        if ("MOL" in data) and (1 <= dump):
            oneFedMol(data["MOL"])

        oneFedHcal(data,
                   patternMode=aux["patternMode"],
                   dump=dump,
                   nonMatched=reduced(nonMatched, fedId),
                   )
    if 1 <= dump:
        print


def htrOverview(d={}):
    abbr = "uHTR" if "uHTR0" in d else "HTR"
    hyphens = "   "+("-"*(67 if (abbr == "uHTR") else 82))
    printer.cyan(hyphens)

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
        printer.cyan(" ".join(line))
    printer.cyan(hyphens)


def oneHtrPatterns(p={}, fedId=None, iOffset=None, patternMode={}):
    cd = htrChannelData(p["channelData"].values(),
                        crate=p["Crate"],
                        slot=p["Slot"],
                        top=p["Top"],
                        fibChs=[1])
    if len(cd) >= 2:
        lines = patternData(p["patternData"],
                            moduleId="%3d %2d" % (fedId, iOffset),
                            slim=patternMode["pureFibersOnly"],
                            process=patternMode["process"],
                            )
        print "\n".join(lines)  # skip printer to facilitate diff


def oneHtr(p={}, iOffset=None, dump=None, utca=None, nonMatched=[]):
    out = []
    if (not iOffset) or (4 <= dump):
        out.append("  ".join(["iWord16",
                              "   EvN",
                              "  OrN5",
                              " BcN",
                              "ModuleId",
                              "FrmtV",
                              #"nWordTP",
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
                          #"  %3d  " % p["nWord16Tp"],
                          "   %3d" % p["nWord16Qie"],
                          "    %2d" % p["nSamples"],
                          "  %2d" % p["nPreSamples"],
                          "  0x%02x" % p["EvN8"],
                          "0x%04x" % p["CRC"],
                          ]))

    printer.green("\n".join(out))
    if 4 <= dump:
        kargs = {"fibChs": [1] if dump == 4 else [0, 1, 2],
                 "nonMatched": reduced(nonMatched, p["ModuleId"]),
                 "latency": p.get("Latency"),
                 }
        if 6 <= dump:
            kargs["skipErrF"] = []
        cd = htrChannelData(p["channelData"].values(),
                            crate=p["Crate"],
                            slot=p["Slot"],
                            top=p["Top"],
                            **kargs)
        if len(cd) >= 2:
            printer.yellow(cd[0])
            printer.msg("\n".join(cd[1:]))

        if 5 <= dump:
            f = (uhtrTriggerData if utca else htrTriggerData)
            td = f(p["triggerData"], skipZero=(dump <= 5))
            if len(td) >= 2:
                printer.yellow(td[0])
                printer.msg("\n".join(td[1:]))


def qieString(qieData={}, red=False):
    l = []
    for iQie in range(12):
        if iQie in qieData:
            l.append("%2x" % qieData[iQie])
        else:
            l.append("  ")

    out = " ".join(l)
    if red:
        out = '\033[91m' + out + '\033[0m'
    return out


def htrTriggerData(d={}, skipZero=False):
    out = ["  ".join(["  Tag", "Peak", "SofI", "TP(hex)  0   1   2   3"])]
    for tag, lst in sorted(d.iteritems()):
        z = ""
        soi = ""
        tp = ""
        if skipZero and not any([dct["TP"] for dct in lst]):
            continue
        for dct in lst:
            z += str(int(dct["Z"]))
            soi += str(int(dct["SOI"]))
            tp += " %3x" % dct["TP"]
        out.append("  ".join([" 0x%02x" % tag,
                              "%4s" % z,
                              "%4s" % soi,
                              " "*4,
                              tp]))
    return out


def uhtrTriggerData(d={}, skipZero=False):
    out = []
    out.append("  ".join([" TPid",
                          "Fl",
                          "  SofI",
                          "   OK",
                          "  TP(hex)",
                          "    ".join([str(i) for i in range(4)])
                          ])
               )
    for channelId, data in sorted(d.iteritems()):
        if skipZero and not any(data["TP"].values()):
            continue
        soi = ""
        ok = ""
        tp = ""
        for j in data["SOI"].keys():
            soi += str(data["SOI"][j])
            ok += str(data["OK"][j])
            tp += "%5x" % data["TP"][j]
        out.append("   ".join([" 0x%02x" % channelId,
                               "%1d" % data["Flavor"],
                               "%5s" % soi,
                               "%5s" % ok,
                               " "*2,
                               tp]))
    return out


def htrChannelData(lst=[], crate=0, slot=0, top="",
                   fibChs=[], skipErrF=[3],
                   nonMatched=[], latency={}):
    out = []
    columns = ["Crate",
               "Slot",
               " Fi",
               "Ch",
               "Fl",
               "ErrF",
               "CapId0",
               "QIE(hex)  0  1  2  3  4  5  6  7  8  9",
    ]
    if latency:
        columns += [" ", " EF", "Cnt", "IDLE"]
    out.append("  ".join(columns))

    for data in lst:
        FiberP1 = 1 + data["Fiber"]
        if data["FibCh"] not in fibChs:
            continue
        if data["ErrF"] in skipErrF:
            continue
        if printer.__color:  # hack
            red = (FiberP1, data["FibCh"]) in nonMatched
        else:
            red = False
        out.append("   ".join(["  %2d" % crate,
                               "%3d%1s" % (slot, top),
                               "%2d" % data["Fiber"],
                               "%1d" % data["FibCh"],
                               "%1d" % data["Flavor"],
                               "%2d" % data["ErrF"],
                               "  %1d" % data["CapId0"],
                               " "*11,
                               ])+qieString(data["QIE"], red=red)
                   )
        if latency:
            dct = latency.get("Fiber%d" % FiberP1)
            if dct:
                lat = ["%s%s" % (dct["Empty"], dct["Full"]),
                       "%3d" % dct["Cnt"],
                       "%4d" % dct["IdleBCN"],
                ]
                out[-1] += "  ".join(lat)

    return out


def patternData(d={}, moduleId="", slim=False, process=False):
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


def oneFedHcal(d={}, patternMode=False, dump=None, nonMatched=[]):
    h = d["header"]
    t = d["trailer"]
    if (not patternMode) and (1 <= dump):
        headers = "   ".join([" FEDid",
                              "  EvN",
                              "       OrN",
                              "    BcN",
                              "minutes",
                              " TTS",
                              " nBytesHW",
                              "nBytesSW",
                              #"CRC16",
                              "nSkip16",
                              ])
        printer.blue("-"*len(headers))
        printer.blue(headers)
        printer.blue("   ".join(["  %3d" % h["FEDid"],
                                 "0x%07x" % h["EvN"],
                                 "0x%08x" % h["OrN"],
                                 "%4d" % h["BcN"],
                                 "%7.3f" % utils.minutes(h["OrN"]),
                                 ("  %1x" % t["TTS"]) if "TTS" in t else "  - ",
                                 ("    %4d" % (t["nWord64"]*8)) if "nWord64" in t else "    --  ",
                                 "    %4d" % d["nBytesSW"],
                                 #(" 0x%04x" % t["CRC16"]) if "CRC16" in t else "   - ",
                                 "%7d" % d["nWord16Skipped"],
                                 ]))
        if 2 <= dump:
            htrOverview(h)

    offsets = d["htrBlocks"].keys()
    if not offsets:
        return
    for iOffset, offset in enumerate(sorted(offsets)):
        p = d["htrBlocks"][offset]
        if "patternData" in p:
            oneHtrPatterns(p=p,
                           patternMode=patternMode,
                           fedId=d["header"]["FEDid"],
                           iOffset=iOffset)
        elif 3 <= dump:  # and 5 <= p["Slot"]:
            oneHtr(p=p, iOffset=iOffset, dump=dump,
                   utca=not configuration.isVme(h["FEDid"]),
                   nonMatched=nonMatched)


def oneFedMol(d):
    printer.blue("--MOL"+("-"*34))
    printer.blue("   ".join([" FEDid  ",
                             "EvN ",
                             "   iBlock",
                             "  nWord64",
                             ]))

    for iBlock in sorted(d.keys()):
        value = d[iBlock]
        printer.blue("   ".join(["  %3d" % value["FEDid"],
                                 "0x%07x" % value["Trigger"],
                                 "%5d" % iBlock,
                                 "    %5d" % value["nWord64"]]))
