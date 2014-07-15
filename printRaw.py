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
    if (not aux["patternMode"]["active"]) and (1 <= dump):
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
    abbr = "HTR" if "HTR0" in d else "uHTR"
    hyphens = "   "+("-"*(67 if (abbr == "uHTR") else 82))
    printer.cyan(hyphens)

    htr = ["  ", "   %4s" % abbr]
    epcv = ["  ", "   EPCV"]
    lms = ["  ", "    LMS"]
    nWord16 = ["  ", "nWord16"]
    for iHtr in range(15):
        key = "%s%d" % (abbr, iHtr)
        if key not in d:
            continue
        h = d[key]
        htr.append("%4d" % iHtr)
        epcv.append("%d%d%d%d" % (h["E"], h["P"], h["C"], h["V"]))
        if "L" in h:
            lms.append(" %d%d%d" % (h["L"], h["M"], h["S"]))
        nWord16.append("%4d" % (h["nWord16"]))

    lines = [htr] + ([lms] if 3 <= len(lms) else []) + [epcv, nWord16]
    for line in lines:
        printer.cyan(" ".join(line))
    printer.cyan(hyphens)


def oneHtrPatterns(p={}, patternMode={}, fedId=None, iOffset=None, utca=None):
    if p["IsTTP"]:
        cd = []
    else:
        cd = htrChannelData(p["channelData"].values(),
                            crate=p["Crate"],
                            slot=p["Slot"],
                            top=p["Top"],
                            fibChs=[1])
    if len(cd) >= 2:
        moduleId = "%3d %2d" % (fedId, p["Slot"] if utca else iOffset)
        lines = patternData(p["patternData"],
                            moduleId=moduleId,
                            utca=utca,
                            slim=patternMode["pureFibersOnly"],
                            )
        print "\n".join(lines)  # skip printer to facilitate diff


def oneHtr(p={}, printColumnHeaders=None, dump=None, utca=None, nonMatched=[]):
    zs = p.get("ZS")

    if "nWord16Qie" in p:
        col = "nWord16Qie"
    else:
        col = "DataLength16"

    out = []
    if printColumnHeaders:
        columns = ["iWord16",
                   "   EvN",
                   "  OrN5",
                   " BcN",
                   "ModuleId",
                   "Fl",
                   "FrmtV",
                   "nPre",
                   #"nWordTP",
                   col,
                   "nSamp",
                   "EvN8",
                   "  CRC",
        ]
        if zs:
            columns += [" ", "ZSMask:  Thr1, Thr24, ThrTP"]
        out.append("  ".join(columns))

    strings = [" %04d" % p["0Word16"],
               " 0x%07x" % p["EvN"],
               "0x%02x" % p["OrN5"],
               "%4d" % p["BcN"],
               "  0x%03x" % p["ModuleId"],
               " %2d" % p.get("FWFlavor", -1),  # absent in uHTR
               " 0x%01x" % p["FormatVer"],
               "  %2d" % p["nPreSamples"],
               #"  %3d  " % p["nWord16Tp"],
               ]
    if "Qie" in col:
        strings.append("     %3d " % p.get(col, -1))
    else:
        s = "    %3d/%3d" % (p.get(col, -1), p.get(col+"T", -1))
        strings.append(s)

    strings += ["   %2d" % p.get("nSamples", -1),  # absent in uHTR
               "  0x%02x" % p["EvN8"],
               "0x%04x" % p["CRC"],
               ]

    if zs:
        strings += ["",
                    "0x%04x" % zs["Mask"],
                    "  %3d" % zs["Threshold1"],
                    "  %3d" % zs["Threshold24"],
                    "  %3d" % zs["ThresholdTP"],
        ]

    out.append("  ".join(strings))
    printer.green("\n".join(out))
    if 4 <= dump:
        kargs = {"fibChs": [1] if dump == 4 else [0, 1, 2],
                 "nonMatched": reduced(nonMatched, p["ModuleId"]),
                 "latency": p.get("Latency"),
                 "zs": p.get("ZS"),
                 "skipErrF": [3],
                 }
        if 6 <= dump:
            kargs["skipErrF"] = []
        if p["IsTTP"]:
            cd = ttpData(p["ttpInput"], p["ttpOutput"], p["ttpAlgoDep"])
        else:
            cd = htrChannelData(p["channelData"].values(),
                                crate=p["Crate"],
                                slot=p["Slot"],
                                top=p["Top"],
                                **kargs)
        if len(cd) >= 2:
            printer.yellow(cd[0])
            printer.msg("\n".join(cd[1:]))

        if 5 <= dump:
            skipZero = dump <= 5
            if utca:
                td = uhtrTriggerData(p["triggerData"], skipZero=skipZero)
            else:
                td = htrTriggerData(p["triggerData"],
                                    skipZero=skipZero,
                                    zs=zs,
                                    )

            if len(td) >= 2:
                printer.yellow(td[0])
                printer.msg("\n".join(td[1:]))


def qieString(qieData={}, red=False):
    l = []
    for iQie in range(10):
        if iQie in qieData:
            l.append("%2x" % qieData[iQie])
        else:
            l.append("  ")

    out = " ".join(l)
    if red:
        out = '\033[91m' + out + '\033[0m'
    return out


def htrTriggerData(d={}, skipZero=False, zs={}):
    columns = ["SLB-ch", "Peak", "SofI", "TP(hex)  0   1   2   3"]
    if zs:
        columns.append("  ZS?")
    out = ["  ".join(columns)]
    for (slb, ch), lst in sorted(d.iteritems()):
        z = ""
        soi = ""
        tp = ""
        if skipZero and not any([dct["TP"] for dct in lst]):
            continue
        for dct in lst:
            z += str(int(dct["Z"]))
            soi += str(int(dct["SOI"]))
            tp += " %3x" % dct["TP"]

        if zs:
            marks = zs["TPMarks"]
            iChannel = 4*(slb - 1) + ch
            if iChannel < len(marks):
                m = "y" if marks[iChannel] else "n"
            else:
                m = " "
            tp += " "*5 + m

        out.append("  ".join(["  %1d- %1d" % (slb, ch),
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
                   fibChs=[], skipErrF=[],
                   nonMatched=[], latency={}, zs={}):
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
    if zs:
        columns += [" ", "ZS?"]
    out.append("  ".join(columns))

    for data in lst:
        if data["FibCh"] not in fibChs:
            continue
        if data["ErrF"] in skipErrF:
            continue
        if printer.__color:  # hack
            red = (data["Fiber"], data["FibCh"]) in nonMatched
        else:
            red = False
        out.append("   ".join([" %3d" % crate,
                               "%3d%1s" % (slot, top),
                               "%2d" % data["Fiber"],
                               "%1d" % data["FibCh"],
                               "%1d" % data["Flavor"],
                               "%2d" % data["ErrF"],
                               "  %1d" % data["CapId0"],
                               "   %2d %s" % (len(data["QIE"]), " "*5)
                               ])+qieString(data["QIE"], red=red)
                   )
        if latency:
            dct = latency.get("Fiber%d" % data["Fiber"])
            if dct and data["FibCh"] == 1:
                lat = [" "*4,
                       "%s%s" % (dct["Empty"], dct["Full"]),
                       "%3d" % dct["Cnt"],
                       "%4d" % dct["IdleBCN"],
                ]
                out[-1] += "  ".join(lat)
        if zs:
            iChannel = 3*data["Fiber"] + data["FibCh"]
            marks = zs["DigiMarks"]
            if iChannel < len(marks):
                m = "y" if marks[iChannel] else "n"
            else:
                m = " "
            out[-1] += "%7s" % m

    return out


def ttpData(ttpInput=[], ttpOutput=[], ttpAlgoDep=[]):
    l = []
    columns = ["TS", "0xhgfedcba9876543210", "0x algo", "0xo"]
    l.append("   ".join(columns))

    for i, (inp, out, algo) in enumerate(zip(ttpInput, ttpOutput, ttpAlgoDep)):
        l.append("   ".join(["%2d" % i,
                             "  %018x" % inp,
                             "  %05x" % algo,
                             "  %1x" % out,
                             ])
                 )
    return l


def patternData(d={}, moduleId="", utca=None, slim=False):
    if slim:
        out = [""]
    else:
        headers = ["ModuleId", "Fibers", "Pattern"]
        chars = " ".join(["%2d" % i for i in range(20)])
        out = ["  ".join(headers+[chars])]

    for fiber1, lst in sorted(d.iteritems()):
        for key in ["A", "B", "C"]:
            if slim and key == "B":
                continue

            ps = patternString(lst, key)
            if not ps:
                continue

            if key == "B":
                fibers = "  %2d,%2d" % (fiber1, 1+fiber1)
            elif key == "A":
                fibers = "     %2d" % (fiber1)
            elif key == "C":
                fibers = "     %2d" % (1 + fiber1)

            if slim:
                fiberNum = int(fibers)
                if not utca:
                    fiberNum += 1
                out.append("%s %2d:  %s" % (moduleId, fiberNum, ps))
            else:
                out.append("   ".join([moduleId, fibers, "  %s" % key, "  "]) + ps)
    return out


def patternString(patterns=[], key=""):
    codes = []
    for p in patterns:
        for k in [key+"0", key+"1"]:
            codes.append(p[k])
    return configuration.patternString(codes)


def oneFedHcal(d={}, patternMode=False, dump=None, nonMatched=[]):
    h = d["header"]
    t = d["trailer"]
    if (not patternMode["active"]) and (1 <= dump):
        fields = [" FEDid",
                  "  EvN",
                  "       OrN",
                  "    BcN",
                  "minutes",
                  " TTS",
                  " nBytesHW",
                  "nBytesSW",
                  #"CRC16",
                  "nSkip16",
                  ]
        if h["uFoV"]:
            fields += ["BcN12", "EvN8", "Blk8"]

        headers = "   ".join(fields)
        printer.blue("-"*len(headers))
        printer.blue(headers)
        sList = ["  %3d" % h["FEDid"],
                 "0x%07x" % h["EvN"],
                 "0x%08x" % h["OrN"],
                 "%4d" % h["BcN"],
                 "%7.3f" % utils.minutes(h["OrN"]),
                 ("  %1x" % t["TTS"]) if "TTS" in t else "  - ",
                 ("    %4d" % (t["nWord64"]*8)) if "nWord64" in t else "    --  ",
                 "    %4d" % d["nBytesSW"],
                 #(" 0x%04x" % t["CRC16"]) if "CRC16" in t else "   - ",
                 "%7d" % d["nWord16Skipped"],
                 ]
        if h["uFoV"]:
            sList += ["   %4d" % t["BcN12"],
                      "0x%02x" % t["EvN8"],
                      "  %2d" % t["Blk_no8"],
                      ]

        printer.blue("   ".join(sList))
        if 2 <= dump:
            htrOverview(h)

    offsets = d["htrBlocks"].keys()
    if not offsets:
        return

    printColumnHeaders = True
    for iOffset, offset in enumerate(sorted(offsets)):
        p = d["htrBlocks"][offset]
        if "patternData" in p:
            oneHtrPatterns(p=p,
                           patternMode=patternMode,
                           fedId=d["header"]["FEDid"],
                           iOffset=iOffset,
                           utca=h["utca"])
        elif 3 <= dump:
            oneHtr(p=p,
                   printColumnHeaders=printColumnHeaders,
                   dump=dump,
                   utca=h["utca"],
                   nonMatched=nonMatched)
            if dump == 3:
                printColumnHeaders = False


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
