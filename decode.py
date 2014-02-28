#AMC13 http://ohm.bu.edu/~hazen/CMS/SLHC/HcalUpgradeDataFormat_v1_2_2.pdf
#DCC2 http://cmsdoc.cern.ch/cms/HCAL/document/CountingHouse/DCC/FormatGuide.pdf
#HTR https://cms-docdb.cern.ch/cgi-bin/PublicDocDB/
#    RetrieveFile?docid=3327&version=14&filename=HTR_MainFPGA.pdf

import configuration
import printer


def ornBcn(ornIn, bcnIn, bcnDelta=0):
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


def header(d={}, iWord64=None, word64=None, utca=None, bcnDelta=0):
    w = word64
    if iWord64 == 0:
        d["FEDid"] = (w >> 8) & 0xfff
        d["BcN"] = (w >> 20) & 0xfff
        d["EvN"] = (w >> 32) & 0xffffff
    if iWord64 == 1:
        d["OrN"] = (w >> 4) & 0xffffffff
        d["OrN"], d["BcN"] = ornBcn(d["OrN"], d["BcN"], bcnDelta)
        d["word16Counts"] = []

    if utca:
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


def payload(d={}, iWord16=None, word16=None, word16Counts=[],
            utca=None, bcnDelta=0, skipFlavors=[], patternMode={}):
    w = word16
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

    #header
    if i == 0:
        l["EvN"] = w & 0xff
        l["nWord16Tp"] = 0  # placeholder; overwritten when i=5
    if i == 1:
        l["EvN"] += w << 8
    if i == 3:
        l["ModuleId"] = w & 0x7ff
        l["OrN5"] = (w >> 11) & 0x1f
    if i == 4:
        l["BcN"] = w & 0xfff
        l["OrN5"], l["BcN"] = ornBcn(l["OrN5"], l["BcN"], bcnDelta)
        l["FormatVer"] = (w >> 12) & 0xf
        assert utca or l["FormatVer"] == 6, "HTR FormatVer %s is not supported." % str(l["FormatVer"])
    if i == 5:
        l["nWord16Tp"] = (w >> 8) & 0xff
        l["nPreSamples"] = (w >> 3) & 0x1f
        l["channelData"] = {}
        l["triggerData"] = {}
    if i < 8 + l["nWord16Tp"]:
        if utca or (i < 8):  # skip various
            return
        tag = (w >> 11) & 0x1f
        if tag not in l["triggerData"]:
            l["triggerData"][tag] = []
        l["triggerData"][tag].append({"Z": (w >> 10) & 0x1,
                                      "SOI": (w >> 9) & 0x1,
                                      "TP": w & 0x1ff,
                                      })
        return

    #trailer
    if i == l["nWord16"]-4:
        l["nWord16Qie"] = w & 0x7ff
        l["nSamples"] = (w >> 11) & 0x1f
        return
    if i == l["nWord16"]-3:
        l["CRC"] = w
        return
    elif i == l["nWord16"]-1:
        if patternMode:
            storePatternData(l, **patternMode)
        d["htrIndex"] += 1
        l["EvN8"] = w >> 8
        l["DTCErrors"] = w & 0xff
        clearChannel(d)  # in case event is malformed
        return

    #skip "extra info"
    if (not utca) and (i >= l["nWord16"]-12):
        return

    #data
    if (w >> 15):
        flavor = (w >> 12) & 0x7
        if flavor in skipFlavors:
            clearChannel(d)
        else:
            dataKey, channelId, channelHeader = channelInit(iWord16=iWord16,
                                                            word16=word16,
                                                            flavor=flavor,
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


def channelInit(iWord16=None, word16=None, flavor=None):
    dataKey = None
    channelId = word16 & 0xff
    channelHeader = {"Flavor": flavor,
                     "CapId0": (word16 >> 8) & 0x3,
                     "ErrF":   (word16 >> 10) & 0x3,
                     "iWord16": iWord16,
                     }

    if flavor == 4:
        dataKey = "triggerData"
        channelHeader.update({"SOI": {},
                              "OK": {},
                              "TP": {},
                              })
    elif flavor in [5, 6]:
        dataKey = "channelData"
        channelHeader.update({"Fiber": channelId / 4,
                              "FibCh": channelId % 4,
                              "QIE": {},
                              "CapId": {},
                              })
    return dataKey, channelId, channelHeader


def storeChannelData(dct={}, iWord16=None, word16=None):
    j = iWord16 - dct["iWord16"] - 1
    if dct["Flavor"] == 4:
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


def storePatternData(l={}, nFibers=None, nTs=None):
    if nFibers == 6:
        offset = 1
    elif nFibers == 8:
        offset = 0
    else:
        assert False, nFibers

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
                        else:
                            printer.error("Cap-ids per time-slice not found.  Run without passing '--patterns'.")
                            exit()
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
