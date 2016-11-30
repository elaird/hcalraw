import printer
import utils


def oneEvent(d={}, nonMatchedQie=[], nonMatchedTp=[], slim1=False):
    if None not in d:
        return

    aux = d[None]
    dump = aux["dump"]

    if dump <= 0:
        return

    if not slim1:
        printer.purple("-" * 85)
        printer.purple("%4s iEntry 0x%08x (%d)" % (aux["label"], aux["iEntry"], aux["iEntry"]))

    printHeaders = not (slim1 and aux["iEntry"])
    for fedId, data in sorted(d.iteritems()):
        if fedId is None:
            continue
        if data["other"]:
            if "magic" in data["other"]:
                oneFedBu(data["other"])
            else:
                oneFedMol(data["other"])

        oneFedHcal(data,
                   dump=dump,
                   crateslots=aux["crateslots"],
                   nonMatchedQie=nonMatchedQie,
                   nonMatchedTp=nonMatchedTp,
                   printHeaders=printHeaders,
                   )
        printHeaders = True
    if not slim1:
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


def spigotList(header):
    out = []
    for key, value in header.iteritems():
        if not key.startswith("HTR"):
            continue
        if not value["nWord16"]:
            continue
        out.append(int(key[3:]))
    return sorted(out)


def oneHtr(p={}, printColumnHeaders=None, dump=None, crateslots=[], utca=None,
           nonMatchedQie=[], nonMatchedTp=[]):
    zs = p.get("ZS")

    if "nWord16Qie" in p:
        col = "nWord16Qie"
    elif utca:
        col = "DataLength16"
    elif p.get("IsTTP"):
        col = "          "
    else:
        coords = "crate %2d slot %2d%1s" % (p.get("Crate", -1), p.get("Slot", -1), p.get("Top", "x"))
        printer.warning("unpacking did not succeed enough to print more about %s" % coords)
        return

    out = []
    if printColumnHeaders:
        columns = ["iWord16",
                   "    EvN",
                   "  OrN5",
                   " BcN",
                   "Cr",
                   "Sl",
                   " Fl",
                   "FrmtV",
                   "nPre",
                   #"nWordTP",
                   col,
                   "nSamp",
                   "EvN8",
                   "  CRC" + ("32" if utca else ""),
        ]
        if zs:
            columns += [" ", "ZSMask:  Thr1, Thr24, ThrTP"]
        out.append("  ".join(columns))

    strings = [" %05d" % p["0Word16"],
               " 0x%07x" % p["EvN"],
               "0x%02x" % p["OrN5"],
               "%4d" % p["BcN"],
               "%2d" % p["Crate"],
               "%2d%1s" % (p["Slot"], p["Top"]),
               "%2d" % p.get("FWFlavor", -1),  # absent in uHTR
               " 0x%01x" % p["FormatVer"],
               "  %2d" % p["nPreSamples"],
               #"  %3d  " % p["nWord16Tp"],
               ]
    if utca:
        s = "  %4d/%4d" % (p.get(col, -1), p.get(col+"T", -1))
        strings.append(s)
    else:
        strings.append("     %3d " % p.get(col, -1))

    strings += ["   %2d" % p.get("nSamples", -1),  # absent in uHTR
                "  0x%02x" % p["EvN8"],
                ]
    if utca:
        strings.append("0x%08x" % p["CRC"])
    elif "Qie" in col:
        strings.append("0x%04x" % p["CRC"])
    else:
        strings.append("  TTP ")

    if zs:
        strings += ["",
                    "0x%04x" % zs["Mask"],
                    "  %3d" % zs["Threshold1"],
                    "  %3d" % zs["Threshold24"],
                    "  %3d" % zs["ThresholdTP"],
        ]

    out.append("  ".join(strings))
    printer.green("\n".join(out))

    anyHtrDataPrinted = False
    if 4 <= dump:
        kargs = {"skipFibChs": [0, 2, 3, 4, 5, 6, 7] if (4 <= dump <= 6) else [],
                 "nonMatched": nonMatchedQie,
                 "latency": p.get("Latency"),
                 "zs": p.get("ZS"),
                 "skipErrF": [3],
                 }
        if dump == 6 or 8 <= dump:
            kargs["skipErrF"] = []
        if p["IsTTP"]:
            cd = ttpData(p["ttpInput"], p["ttpOutput"], p["ttpAlgoDep"])
        else:
            if crateslots and (100*p["Crate"] + p["Slot"]) not in crateslots:
                return
            cd = htrChannelData(p["channelData"].values(),
                                crate=p["Crate"],
                                slot=p["Slot"],
                                top=p["Top"],
                                **kargs)
        if len(cd) >= 2:
            printer.yellow(cd[0])
            printer.msg("\n".join(cd[1:]))
            anyHtrDataPrinted = True

        if 5 <= dump:
            kargs = {"skipZeroTps": dump <= 7,
                     "crate": p["Crate"],
                     "slot": p["Slot"],
                     "top": p["Top"],
                     "nonMatched": nonMatchedTp,
                     }
            if utca:
                td = uhtrTriggerData(p["triggerData"], **kargs)
            else:
                td = htrTriggerData(p["triggerData"], zs=zs, **kargs)

            if len(td) >= 2:
                printer.yellow(td[0])
                printer.msg("\n".join(td[1:]))
                anyHtrDataPrinted = True

    return anyHtrDataPrinted


def makeRed(s):
    if printer.__color:  # hack
        return '\033[91m' + s + '\033[0m'
    else:
        return s


def qieString(qies=[], red=False):
    l = []
    for i in range(10):
        if i < len(qies):
            l.append("%2x" % qies[i])
        else:
            l.append("  ")

    out = " ".join(l)
    if red:
        out = makeRed(out)
    return out


def htrTriggerData(d={}, skipZeroTps=False, crate=None, slot=None, top="", nonMatched=[], zs={}):
    columns = ["SLB-ch", "Peak", "SofI", "TP(hex)  0   1   2   3"]
    if zs:
        columns.append("  ZS?")
    out = ["  ".join(columns)]
    for key, dct in sorted(d.iteritems()):
        slb, ch = key
        z = ""
        soi = ""
        tp = ""
        if skipZeroTps and not any([dct["TP"]]):
            continue

        for i in range(len(dct["TP"])):
            z += str(int(dct["Z"][i]))
            soi += str(int(dct["SOI"][i]))
            tp += " %3x" % dct["TP"][i]

        if zs:
            marks = zs["TPMarks"]
            iChannel = 4*(slb - 1) + ch
            if iChannel < len(marks):
                m = "y" if marks[iChannel] else "n"
            else:
                m = " "
            tp += " "*5 + m

        one = "  ".join(["  %1d- %1d" % (slb, ch),
                         "%4s" % z,
                         "%4s" % soi,
                         " "*4,
                         tp])
        if (crate, slot, top, key) in nonMatched:
            one = makeRed(one)
        out.append(one)

    return out


def uhtrTriggerData(d={}, skipZeroTps=False, crate=None, slot=None, top="", nonMatched=[]):
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
        if skipZeroTps and not any(data["TP"]):
            continue
        soi = ""
        ok = ""
        tp = ""
        for j in range(len(data["SOI"])):
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
                   skipFibChs=[], skipErrF=[],
                   nonMatched=[], latency={}, zs={},
                   utcaFiberBlackList=[0,1,10,11,12,13,22,23][:0],
                   te_tdc=False):
    out = []
    columns = ["Crate",
               "Slot",
               "Fi",
               "Ch",
               "Fl",
               "ErrF",
               "Cap0",
               "NS 0xA0 A1 A2 A3 A4 A5 A6 A7 A8 A9",
               "0xL0 L1 L2 L3 L4 L5 L6 L7 L8 L9",
               ]
    if te_tdc:
        columns += [" T0 T1 T2 T3 T4 T5 T6 T7 T8 T9"]
    if latency:
        columns += [" ", " EF", "Cnt", "IDLE"]
    if zs:
        columns += [" ", "ZS?"]
    out.append(" ".join(columns))

    for data in sorted(lst, key=lambda x: (x["Fiber"], x["FibCh"])):
        if (top not in "tb") and data["Fiber"] in utcaFiberBlackList:
            continue
        if data["FibCh"] in skipFibChs:
            continue
        if data["ErrF"] in skipErrF:
            continue
        red = (crate, slot, top, data["Fiber"], data["FibCh"]) in nonMatched

        fields = [" %3d" % crate,
                  "  %2d%1s" % (slot, top),
                  "%2d" % data["Fiber"],
                  " %1d" % data["FibCh"],
                  " %1d" % data["Flavor"],
                  " %2d" % data["ErrF"],
                  "  %1d" % data["CapId0"],
                  "  %2d   " % len(data["QIE"]) + qieString(data["QIE"], red=red),
                  "  " + qieString(data.get("TDC", []))
                  ]
        if te_tdc:
            fields += [qieString(data.get("TDC_TE", []))]
        out.append(" ".join(fields))

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
            iChannel = 3*(data["Fiber"] - 1) + data["FibCh"]
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


def oneFedHcal(d={}, dump=None, crateslots=[],
               nonMatchedQie=[], nonMatchedTp=[],
               printHeaders=None):
    h = d["header"]
    t = d["trailer"]
    if (1 <= dump):
        fields = [" FEDid",
                  "  EvN",
                  "       OrN",
                  "    BcN",
                  "minutes",
                  " TTS",
                  "nBytesHW(   SW)",
                  #"CRC16",
                  "nSkip16",
                  "BcN12",
                  "EvN8",
                  "Blk8",
                  ]

        if printHeaders:
            headers = "  ".join(fields)
            printer.blue("-" * len(headers))
            printer.blue(headers)

        sList = [" %4d" % h["FEDid"],
                 "0x%07x" % h["EvN"],
                 "0x%08x" % h["OrN"],
                 "%4d" % h["BcN"],
                 "%7.3f" % utils.minutes(h["OrN"], h["BcN"]),
                 ("  %1x" % t["TTS"]) if "TTS" in t else "  - ",
                 "    %5d(%5d)" % (t["nWord64"]*8 if "nWord64" in t else "  -1", d["nBytesSW"]),
                 #(" 0x%04x" % t["CRC16"]) if "CRC16" in t else "   - ",
                 "%7d" % d["nWord16Skipped"],
                 ]
        if h["uFoV"]:
            sList += [" %4d" % t["BcN12"],
                      "0x%02x" % t["EvN8"],
                      "  %2d" % t["Blk_no8"],
                      ]

        printer.blue("  ".join(sList))
        if 2 <= dump:
            htrOverview(h)

    printColumnHeaders = True
    for iBlock, block in sorted(d["htrBlocks"].iteritems()):
        try:  # FIXME
           isPattern = "patternData" in block
        except TypeError as e:
            print "iBlock='%s':" % str(iBlock), e
            continue

        if 3 <= dump:
            printColumnHeaders = oneHtr(p=block,
                                        printColumnHeaders=printColumnHeaders,
                                        dump=dump,
                                        crateslots=crateslots,
                                        utca=h["utca"],
                                        nonMatchedQie=nonMatchedQie,
                                        nonMatchedTp=nonMatchedTp,
                                        )


def oneFedMol(d):
    header = "   ".join([" FEDid  ",
                             "EvN ",
                             "   iBlock",
                             "  nWord64",
                             "magic",
                             ])
    printer.blue("--MOL" + ("-" * len(header)))
    printer.blue(header)

    for iBlock, value in sorted(d.iteritems()):
        printer.blue("   ".join(["  %3d" % value["FEDid"],
                                 "0x%07x" % value["Trigger"],
                                 "%5d" % iBlock,
                                 "    %5d" % value["nWord64"],
                                 "   %4x" % value["magic"],
                             ]))


def oneFedBu(d):
    header = "   ".join(["magic".rjust(12), "nWord64".rjust(15)])
    printer.blue("--wrapper" + ("-" * len(header)))
    printer.blue(header)
    printer.blue("0x%16x   %7d" % (d["magic"], d["nWord64"]))
