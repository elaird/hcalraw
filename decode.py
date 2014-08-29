# AMC13 (May 2014 onward) http://ohm.bu.edu/~hazen/CMS/AMC13/UpdatedDAQPath_2014-05-01.pdf
# uHTR  (May 2014 onward) https://cms-docdb.cern.ch/cgi-bin/DocDB/RetrieveFile?docid=12306&version=2&filename=uhtr_spec.pdf
# AMC13/uHTR (through April 2014) http://ohm.bu.edu/~hazen/CMS/SLHC/HcalUpgradeDataFormat_v1_2_3.pdf
# DCC2 http://cmsdoc.cern.ch/cms/HCAL/document/CountingHouse/DCC/FormatGuide.pdf
# HTR https://cms-docdb.cern.ch/cgi-bin/PublicDocDB/RetrieveFile?docid=3327&version=14&filename=HTR_MainFPGA.pdf
# TTP http://cmsdoc.cern.ch/cms/HCAL/document/Aux/HcalTechTriggerProcessor/dataformat.html


import configuration
import printer
import sys


def ornBcn(ornIn, bcnIn, utca):
    bcnDelta = configuration.bcnDelta(utca)

    if not bcnDelta:
        return ornIn, bcnIn

    orn = ornIn
    bcn = bcnIn + bcnDelta
    if bcn < 0:
        bcn += 3564
        orn -= 1
    if bcn > 3563:
        bcn -= 3564
        orn += 1
    return orn, bcn


def trailer(d={}, iWord64=None, word64=None):
    d["TTS"] = (word64 >> 4) & 0xf
    d["CRC16"] = (word64 >> 16) & 0xffff
    d["nWord64"] = (word64 >> 32) & 0xffffff


def htrDict(w, l=[]):
    nWord16 = 2*(w & 0x3ff)
    if nWord16:
        l.append(nWord16)
    return {"nWord16": nWord16,
            "E": (w >> 15) & 1,
            "P": (w >> 14) & 1,
            "C": (w >> 10) & 1,
            "V": not ((w >> 12) & 1 or (w >> 13) & 1),
            }


def uHtrDict(w, l=[]):
    nWord16 = w & 0xfff
    if nWord16:
        l.append(nWord16)
    return {"nWord16": nWord16,
            "E": (w >> 15) & 1,
            "P": (w >> 14) & 1,
            "V": (w >> 13) & 1,
            "C": (w >> 12) & 1,
            }


def header(d={}, iWord64=None, word64=None):
    w = word64
    if iWord64 == 0:
        #d["FoV"] = (w >> 4) & 0xf
        d["FEDid"] = (w >> 8) & 0xfff
        d["BcN"] = (w >> 20) & 0xfff
        d["EvN"] = (w >> 32) & 0xffffff
        #d["Evt_ty"] = (w >> 56) & 0xf
        return

    if iWord64 == 1:
        d["uFoV"] = (w >> 60) & 0xf

    if d["uFoV"]:
        block_header_ufov1(d=d, iWord64=iWord64, word64=word64)
    else:
        header_ufov0(d=d, iWord64=iWord64, word64=word64)


def block_header_ufov1(d={}, iWord64=None, word64=None):
    w = word64
    if iWord64 == 1:
        d["word16Counts"] = []
        d["utca"] = True

        d["OrN"] = (w >> 4) & 0xffffffff
        d["OrN"], d["BcN"] = ornBcn(d["OrN"], d["BcN"], d["utca"])

        d["nAMC"] = (w >> 52) & 0xf
        d["iWordPayload0"] = 2 + d["nAMC"]
        return

    if iWord64 < d["iWordPayload0"]:
        iAMC = (w >> 16) & 0xf
        key = "uHTR%d" % iAMC
        d[key] = {}

        lmsepvc = (w >> 56) & 0x7f
        for i, l in enumerate(["L", "M", "S", "E", "P", "V", "C"]):
            d[key][l] = (lmsepvc >> (6-i)) & 0x1
        if d[key]["M"]:
            sys.exit("multi-block unpacking not implemented")
        d[key]["BoardID"] = w & 0xffff
        d[key]["Blk_no"] = (w >> 20) & 0xff
        d[key]["nWord16"] = (w >> 32) & 0xffffff
        d[key]["nWord16"] *= 4
        d["word16Counts"].append(d[key]["nWord16"])


def block_trailer_ufov1(d={}, iWord64=None, word64=None):
    d["BcN12"] = word64 & 0xfff
    _, d["BcN12"] = ornBcn(0, d["BcN12"], True)
    d["EvN8"] = (word64 >> 12) & 0xff
    d["Blk_no8"] = (word64 >> 20) & 0xff
    d["CRC32"] = word64 >> 32


def header_ufov0(d={}, iWord64=None, word64=None):
    w = word64
    if iWord64 == 1:
        d["OrN"] = (w >> 4) & 0xffffffff
        d["word16Counts"] = []
        return

    if iWord64 == 2:
        d["FormatVersion"] = w & 0xff
        d["utca"] = 0x10 <= d["FormatVersion"]
        d["iWordPayload0"] = 6 if d["utca"] else 12
        d["OrN"], d["BcN"] = ornBcn(d["OrN"], d["BcN"], d["utca"])

    if d["utca"]:
        if 3 <= iWord64 <= 5:
            uhtr0 = 4*(iWord64-3)
            for i in range(4):
                d["uHTR%d" % (uhtr0+i)] = uHtrDict((w >> (16*i)) & 0xffff,
                                                   d["word16Counts"])
    else:
        if 3 <= iWord64 <= 10:
            j = (iWord64-3)*2
            d["HTR%d" % j] = htrDict(w, d["word16Counts"])
            if iWord64 != 10:
                d["HTR%d" % (j+1)] = htrDict(w >> 32, d["word16Counts"])


def MOLheader(d={}, word64_1=None, word64_2=None):
    w1 = word64_1
    w2 = word64_2
    iblock = (w1 >> 32) & 0x7ff
    d[iblock] = {}
    d[iblock]["isFirstBlock"] = w1 & (1L << 31)
    d[iblock]["isLastBlock"] = w1 & (1L << 30)
    d[iblock]["nWord64"] = w1 & 0x3ff
    d[iblock]["FEDid"] = (w2 >> 32) & 0xfff
    d[iblock]["Trigger"] = w2 & 0xffffff


def htrHeaderV1(l={}, w=None, i=None, utca=None):
    if i == 0:
        l["DataLength16"] = w

    if i == 1:
        l["DataLength16"] |= (w & 0xf) << 16
        l["DataLength16"] *= 4
        l["BcN"] = w >> 4

    if i == 2:
        l["EvN"] = w

    if i == 3:
        l["EvN"] |= (w & 0xff) << 16

    if i == 4:
        l["nPreSamples"] = (w >> 12) & 0xf
        l["Slot"] = (w >> 8) & 0xf
        l["Crate"] = w & 0xff
        # compat
        l["ModuleId"] = 0
        l["Top"] = " "

    if i == 5:
        l["OrN"] = w
        l["OrN5"] = l["OrN"] & 0x1f  # compat
        l["OrN"], l["BcN"] = ornBcn(l["OrN"], l["BcN"], True)

    if i == 6:
        l["PayloadFormat"] = (w >> 12) & 0xf
        l["EventType"] = (w >> 8) & 0xf
        l["FwFlavor"] = w & 0xff
        l["FormatVer"] = l["PayloadFormat"]  # compat

    if i == 7:
        l["Header7"] = w

    l["IsTTP"] = False
    l["channelData"] = {}
    l["triggerData"] = {}


def htrHeaderV0(l={}, w=None, i=None, utca=None):
    if i == 0:
        l["EvN"] = w & 0xff

    if i == 1:
        l["EvN"] += w << 8

    if i == 2 and not utca:
        l["HM"] = (w >> 13) & 0x1
        l["EE"] = (w >> 2) & 0x1

    if i == 3:
        l["OrN5"] = (w >> 11) & 0x1f
        l["ModuleId"] = w & 0x7ff
        if utca:
            l["Crate"] = l["ModuleId"] >> 4
            l["Slot"] = l["ModuleId"] & 0xf
            l["Top"] = " "
        else:
            # https://svnweb.cern.ch/cern/wsvn/cmshcos/trunk/hcalHW/src/common/hcalHTR.cc
            # int id=(m_crate<<6)+((m_slot&0x1F)<<1)+((true_for_top)?(1):(0));
            # fpga->dev->write("HTRsubmodN",id);
            l["Crate"] = l["ModuleId"] >> 6
            l["Slot"] = (l["ModuleId"] >> 1) & 0x1f
            l["Top"] = "t" if (l["ModuleId"] & 0x1) else "b"

    if i == 4:
        l["BcN"] = w & 0xfff
        l["OrN5"], l["BcN"] = ornBcn(l["OrN5"], l["BcN"], utca)
        l["FormatVer"] = (w >> 12) & 0xf
        l["UnsupportedFormat"] = (not utca) and (l["FormatVer"] != 6)

    if i == 5:
        l["channelData"] = {}
        l["triggerData"] = {}
        if utca:
            #l["nWord16Payload"] = w & 0x1fff  # !document
            l["nPreSamples"] = (w >> 3) & 0x1f  # !document
        else:
            l["nWord16Tp"] = (w >> 8) & 0xff
            l["nPreSamples"] = (w >> 3) & 0x1f

    if i == 6:
        l["US"] = (w >> 15) & 0x1
        l["CM"] = (w >> 14) & 0x1

    if i == 7:
        l["IsTTP"] = (w >> 15) & 0x1
        l["PipelineLength"] = w & 0xff
        if l["IsTTP"]:
            l["TTPAlgo"] = (w >> 8) & 0x7
            for key in ["Crate", "Slot", "Top", "UnsupportedFormat"]:
                del l[key]
        else:
            l["FWFlavor"] = (w >> 8) & 0x7f
            if l["UnsupportedFormat"]:
                c =  "(crate %2d slot %2d%1s)" % (l["Crate"], l["Slot"], l["Top"])
                printer.error("HTR %s FormatVer %d is not supported." % (c, l["FormatVer"]))


def htrTps(l={}, w=None):
    tag = (w >> 11) & 0x1f
    slb = (tag >> 2) & 0x7
    ch = tag & 0x3
    key = (slb, ch)
    if key not in l["triggerData"]:
        l["triggerData"][key] = []
    l["triggerData"][key].append({"Z": (w >> 10) & 0x1,
                                  "SOI": (w >> 9) & 0x1,
                                  "TP": w & 0x1ff,
                              })


def htrExtra(l={}, w=None, i=None):
    if l["US"]:
        if "ZS" not in l:
            l["ZS"] = {}
        if i == 1:
            l["ZS"]["DigiMarks"] = []
            l["ZS"]["TPMarks"] = []

        if i <= 3:
            digi = w & 0xff
            tp = (w >> 8) & 0xff
            for iBit in range(8):
                l["ZS"]["DigiMarks"].append((digi >> iBit) & 0x1)
                l["ZS"]["TPMarks"].append((tp >> iBit) & 0x1)

        if i == 4:
            l["ZS"]["Threshold1"] = w & 0xff
            l["ZS"]["Threshold24"] = (w >> 8) & 0xff
        if i == 5:
            l["ZS"]["ThresholdTP"] = (w >> 12) & 0xf
        if i == 6:
            t = (w >> 12) & 0xf
            l["ZS"]["ThresholdTP"] |= (t << 4)
        if i == 7:
            m = (w >> 12) & 0x7
            l["ZS"]["Mask"] = (m << 16)
        if i == 8:
            l["ZS"]["Mask"] |= w
    else:
        if "Latency" not in l:
            l["Latency"] = {}

        key = "Fiber%d" % i
        l["Latency"][key] = {"Empty": (w >> 15) & 0x1,
                             "Full": (w >> 14) & 0x1,
                             "Cnt": (w >> 12) & 0x3,
                             "IdleBCN": w & 0x3ff,
                             }


def htrPreTrailer(l={}, w=None, k=None):
    if k == 4:
        l["nWord16Qie"] = w & 0x7ff
        l["nSamples"] = (w >> 11) & 0x1f
    if k == 3:
        l["CRC"] = w


def end(d, l, patternMode):
    d["htrIndex"] += 1
    if patternMode["active"]:
        storePatternData(l, **patternMode)
    clearChannel(d)  # in case event is malformed


def payload(d={}, iWord16=None, word16=None, word16Counts=[],
            utca=None, skipFlavors=[], patternMode={}, dump=0):

    if 8 <= dump:
        print "      (%5d 0x%04x)" % (iWord16, word16)

    if "htrIndex" not in d:
        for iHtr in range(len(word16Counts)):
            d[iHtr] = {"nWord16": word16Counts[iHtr]}
        d["htrIndex"] = 0

    if d["htrIndex"] in d:
        l = d[d["htrIndex"]]
    else:
        return iWord16

    if "0Word16" not in l:
        l["0Word16"] = iWord16

    i = iWord16 - l["0Word16"]

    if i < 8:
        if not i:
            l["headerWords"] = []
        l["headerWords"].append(word16)
        if i == 7:
            l["V1"] = (l["headerWords"][6] >> 12) & 0x1
            l["V1"] &= utca
            func = htrHeaderV1 if l["V1"] else htrHeaderV0
            for iHeaderWord in range(8):
                func(l, w=l["headerWords"][iHeaderWord], i=iHeaderWord, utca=utca)
            del l["headerWords"]
        return

    k = l["nWord16"] - i

    if k == 3 and utca and not l["V1"]:  # !document
        l["CRC"] = word16
        return

    if l["V1"] and k <= 4:
        if k == 4:
            l["DataLength16T"] = word16
        if k == 3:
            l["DataLength16T"] |= (word16 & 0xf) << 16
            l["DataLength16T"] *= 4
            l["EvN8"] = word16 >> 8
        if k == 2:
            l["CRC"] = word16
        if k == 1:
            l["CRC"] |= word16 << 16
            end(d, l, patternMode)

        return

    if (not l["V1"]) and k <= 2:
        if k == 1:
            l["EvN8"] = word16 >> 8
            end(d, l, patternMode)
        return


    if l["IsTTP"]:
        ttpData(l, (i - 8) % 6, word16)
    else:
        if not utca:
            if i < 8 + l["nWord16Tp"]:
                htrTps(l, word16)
                return

            if (3 <= k <= 4):
                htrPreTrailer(l, word16, k)
                return

            if (5 <= k <= 12) and not l["CM"]:
                htrExtra(l, w=word16, i=13-k)
                return

        htrData(d=d,
                l=l,
                iWord16=iWord16,
                word16=word16,
                skipFlavors=skipFlavors,
                patternMode=patternMode,
                utca=utca,
                )


def ttpData(l={}, iDataMod6=None, word16=None):
    if "ttpInput" not in l:
        l["ttpInput"] = []
        l["ttpAlgoDep"] = []
        l["ttpOutput"] = []

    if not iDataMod6:
        for key in ["ttpInput", "ttpAlgoDep", "ttpOutput"]:
            l[key].append(0)

    if iDataMod6 <= 3:
        l["ttpInput"][-1] |= word16 << (iDataMod6 * 16)
    if iDataMod6 == 4:
        l["ttpInput"][-1] |= (word16 & 0xff) << (iDataMod6 * 16)
        l["ttpAlgoDep"][-1] = word16 >> 8
    if iDataMod6 == 5:
        l["ttpAlgoDep"][-1] |= (word16 & 0xfff) << 8
        l["ttpOutput"][-1] = (word16 >> 12) & 0xf


def htrData(d={}, l={}, iWord16=None, word16=None, skipFlavors=[], patternMode={}, utca=None):
    if (word16 >> 15):
        flavor = (word16 >> 12) & 0x7
        if flavor in skipFlavors:
            clearChannel(d)
        else:
            dataKey, channelId, channelHeader = channelInit(iWord16=iWord16,
                                                            word16=word16,
                                                            flavor=flavor,
                                                            utca=utca,
                                                            )
            if dataKey is None:
                printer.warning("skipping flavor %d (EvN %d, iWord16 %d)." % (flavor, l["EvN"], iWord16))
                clearChannel(d)
            else:
                d["dataKey"] = dataKey
                d["channelId"] = channelId
                l[d["dataKey"]][d["channelId"]] = channelHeader
    elif "channelId" in d:
        storeChannelData(dct=l[d["dataKey"]][d["channelId"]],
                         iWord16=iWord16,
                         word16=word16,
                         )


def clearChannel(d):
    for key in ["channelId", "dataKey"]:
        if key in d:
            del d[key]


def channelInit(iWord16=None, word16=None, flavor=None, utca=None):
    dataKey = None
    channelId = word16 & 0xff
    channelHeader = {"Flavor": flavor,
                     "CapId0": (word16 >> 8) & 0x3,
                     "ErrF":   (word16 >> 10) & 0x3,
                     "iWord16": iWord16,
                     }

    if flavor == 4:
        dataKey = "triggerData"
        for key in ["SOI", "OK", "TP"]:
            channelHeader[key] = {}

    elif flavor != 7:
        dataKey = "channelData"
        channelHeader["Fiber"] = channelId / 4
        if not utca:
            channelHeader["Fiber"] += 1

        channelHeader["FibCh"] = channelId % 4
        channelHeader["QIE"] = {}
        channelHeader["CapId"] = {}

        if 0 <= flavor <= 1:
            for key in ["SOI", "TDC"]:
                channelHeader[key] = {}
        if 2 <= flavor <= 3:
            for key in ["SOI", "OK", "TDCRise", "TDCFall"]:
                channelHeader[key] = {}

    return dataKey, channelId, channelHeader


def storeChannelData(dct={}, iWord16=None, word16=None):
    j = iWord16 - dct["iWord16"] - 1
    if 0 <= dct["Flavor"] <= 1:
        dct["SOI"][j] = (word16 >> 14) & 0x1
        dct["TDC"][j] = (word16 >> 8) & 0x3f
        dct["QIE"][j] = word16 & 0xff
    elif 2 <= dct["Flavor"] <= 3:
        k = j / 2
        if j % 2:
            dct["TDCRise"][k] = word16 & 0x3f
            dct["TDCFall"][k] = (word16 >> 6) & 0x3f
        else:
            dct["SOI"][k] = (word16 >> 13) & 0x1
            dct["OK"][k] = (word16 >> 12) & 0x1
            dct["QIE"][k] = word16 & 0xff
    elif dct["Flavor"] == 4:
        dct["SOI"][j] = (word16 >> 14) & 0x1
        dct["OK"][j] = (word16 >> 13) & 0x1
        dct["TP"][j] = word16 & 0x1fff
    elif dct["Flavor"] == 5:
        dct["QIE"][2*j] = word16 & 0x7f
        dct["QIE"][2*j+1] = (word16 >> 8) & 0x7f
    elif dct["Flavor"] == 6:
        dct["QIE"][j] = word16 & 0x7f
        dct["CapId"][j] = (word16 >> 8) & 0x3


def channelId(fiber=None, fibCh=None):
    return 4*fiber + fibCh


def storePatternData(l={}, nFibers=None, nTs=None, compressed=None, rmRibbon=None, **_):
    offset = 1 if rmRibbon else 0

    l["patternData"] = {}
    d = l["channelData"]

    for iFiberPair in range(nFibers/2):
        fiber1 = 2*iFiberPair + offset
        fiber2 = 2*iFiberPair + 1 + offset
        l["patternData"][fiber1] = []

        for iTs in range(nTs):
            feWords = []
            # Tullio says HTR f/w makes no distinction between optical cables 1 and 2
            for fiber in [fiber1, fiber2]:
                feWord32 = 0
                for fibCh in range(3):
                    key = channelId(fiber, fibCh)
                    if key in d:
                        qies = d[key]["QIE"]
                        try:
                            qie = qies[iTs]
                        except KeyError:
                            #printer.warning("time slice %d not found:" % iTs, sorted(qies.keys()))
                            continue
                        if d[key]["CapId"]:
                            cap = d[key]["CapId"][iTs]
                        elif not compressed:
                            sys.exit("Cap-ids per time-slice not found.  Either pass '--compressed' or do not pass '--patterns'.")
                        else:
                            cap = 0
                        if fibCh == 0:
                            feWord32 |= qie << 25
                            feWord32 |= cap << 7
                        if fibCh == 1:
                            feWord32 |= qie << 17
                            feWord32 |= cap << 5
                        if fibCh == 2:
                            feWord32 |= qie << 9
                            feWord32 |= cap << 3

                feWords.append(feWord32)
                #print "iFiberPair =", iFiberPair, "iTs =", iTs, "qie0 =", hex(qie0), "feWord =", feWord32_1
            l["patternData"][fiber1].append(patternData(feWords))


def patternData(feWords=[]):
    assert len(feWords) == 2, len(feWords)

    A0 = (feWords[0] >> 24) & 0xfe
    A0 |= (feWords[0] >> 7) & 0x1

    A1 = (feWords[0] >> 17) & 0x7f
    A1 |= (feWords[0] >> 1) & 0x80

    B0 = (feWords[0] >> 8) & 0xfe
    B0 |= (feWords[0] >> 3) & 0x1

    B1 = (feWords[1] >> 9) & 0xfe
    B1 |= (feWords[0] << 3) & 0x80

    C0 = (feWords[1] >> 24) & 0xfe
    C0 |= (feWords[1] >> 7) & 0x1

    C1 = (feWords[1] >> 17) & 0x7f
    C1 |= (feWords[1] >> 1) & 0x80

    return {"A0": flipped(A0),
            "A1": flipped(A1),
            "B0": flipped(B0),
            "B1": flipped(B1),
            "C0": flipped(C0),
            "C1": flipped(C1),
            }


def flipped(raw=None, nBits=8):
    out = 0
    for iBit in range(nBits):
        bit = (raw >> iBit) & 0x1
        out |= (bit << (nBits - 1 - iBit))
    return out
