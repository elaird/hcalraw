# QIE  8: https://cms-docdb.cern.ch/cgi-bin/PublicDocDB/RetrieveFile?docid=3327&version=14&filename=HTR_MainFPGA.pdf
# errata: http://cmsonline.cern.ch/cms-elog/807780
#
# QIE 10: https://svnweb.cern.ch/trac/cms-firmwsrc/browser/hcal/HF_RM_igloo2/trunk/docs/HF_RM_DataFormat.txt
# QIE 11: 

import configuration.hw
import configuration.patterns
from printRaw import spigotList


def patterns(raw1={}, **_):
    for fedId, raw in sorted(raw1.iteritems()):
        if fedId is None:
            continue

        for iBlock, block in sorted(raw["htrBlocks"].iteritems()):
            if block["IsTTP"]:
                continue

            # skip printer to facilitate diff
            print "\n".join(lines(raw["header"], iBlock, block))


def lines(h, iBlock, block):
    if h["utca"]:
        moduleId = "u%2d %2d" % (block["Crate"], block["Slot"])
    else:
        moduleId = "%3d %2d" % (h["FEDid"], spigotList(h)[iBlock])

    if configuration.patterns.patternB:
        headers = [configuration.patterns.lineStart, "ModuleId", "Fibers", "Pattern"]
        chars = " ".join(["%2d" % i for i in range(20)])
        out = ["  ".join(headers + [chars])]
    else:
        out = [""]

    # print "Crate=%2d, Slot=%2d" % (block["Crate"], block["Slot"])
    d = storePatternData(block["channelData"], h["utca"])

    for fiber1, lst in sorted(d.iteritems()):
        out += lines_fiber_pair(fiber1, lst, h["utca"], moduleId)

    return out


def lines_fiber_pair(fiber1, lst, utca, moduleId):
    descr = configuration.patterns.lineStart

    out = []
    for key in ["A", "B", "C"]:
        if (not configuration.patterns.patternB) and key == "B":
            continue

        if key == "B":
            fibers = "%2d,%2d" % (fiber1, 1 + fiber1)
        elif key == "A":
            fibers = "   %2d" % (fiber1)
        elif key == "C":
            fibers = "   %2d" % (1 + fiber1)

        ps = patternString(lst, key)
        if ps is None:
            continue

        if configuration.patterns.patternB:
            out.append("   ".join([descr, moduleId, fibers, "   %s" % key, "  "]) + ps)
        else:
            fiberNum = int(fibers)
            out.append("%s %2d:  %s" % (descr + moduleId, int(fibers), ps))

    return out


def patternString(patterns=[], key=""):
    codes = []
    for p in patterns:
        c0 = p.get(key + "0")
        c1 = p.get(key + "1")
        if c0 is None or c1 is None:
            break
        else:
            codes += [c0, c1]

    if codes:
        return configuration.patterns.string(codes)
    else:
        return None


def feWord(d, fiber, iTs):
    word = None

    for key, v in d.iteritems():
        if v["Fiber"] != fiber:
            continue

        if v["ErrF"] == 3:  # 8b/10b errors
            continue

        if len(v["QIE"]) <= iTs:
            continue

        if 5 <= v["Flavor"] <= 6:
            word = qie8(word, v, iTs)
        elif 0 <= v["Flavor"] <= 1:
            pass
        elif v["Flavor"] == 2:
            word = qie10(word, v, iTs)

    return word


def qie10(feWord80, dct, iTs):
    fibCh = dct["FibCh"]

    if feWord80 is None:
        feWord80 = 0

    if fibCh == 0:
        feWord80 |= ( dct["TDC_TE"][iTs]    &  0xf ) <<  0
        feWord80 |= ( dct["CapId"][iTs]     &  0x3 ) <<  8
        feWord80 |= ( dct["QIE"][iTs]       & 0xff ) << 16
        feWord80 |= ((dct["TDC"][iTs] >> 4) &  0x3 ) << 48
        feWord80 |= ((dct["TDC"][iTs] >> 2) &  0x3 ) << 56
        feWord80 |= ((dct["TDC"][iTs] >> 0) &  0x3 ) << 64
    if fibCh == 1:
        feWord80 |= ( dct["TDC_TE"][iTs]    &  0xf ) <<  4
        feWord80 |= ( dct["CapId"][iTs]     &  0x3 ) << 10
        feWord80 |= ( dct["QIE"][iTs]       & 0xff ) << 24
        feWord80 |= ((dct["TDC"][iTs] >> 4) &  0x3 ) << 50
        feWord80 |= ((dct["TDC"][iTs] >> 2) &  0x3 ) << 58
        feWord80 |= ((dct["TDC"][iTs] >> 0) &  0x3 ) << 66
    if fibCh == 2:
        feWord80 |= ( dct["CapId"][iTs]     &  0x3 ) << 12
        feWord80 |= ( dct["QIE"][iTs]       & 0xff ) << 32
        feWord80 |= ((dct["TDC"][iTs] >> 4) &  0x3 ) << 52
        feWord80 |= ((dct["TDC"][iTs] >> 2) &  0x3 ) << 60
        feWord80 |= ((dct["TDC"][iTs] >> 0) &  0x3 ) << 68
        feWord80 |= ( dct["TDC_TE"][iTs]    &  0xf ) << 72
    if fibCh == 3:
        feWord80 |= ( dct["CapId"][iTs]     &  0x3 ) << 14
        feWord80 |= ( dct["QIE"][iTs]       & 0xff ) << 40
        feWord80 |= ((dct["TDC"][iTs] >> 4) &  0x3 ) << 54
        feWord80 |= ((dct["TDC"][iTs] >> 2) &  0x3 ) << 62
        feWord80 |= ((dct["TDC"][iTs] >> 0) &  0x3 ) << 70
        feWord80 |= ( dct["TDC_TE"][iTs]    &  0xf ) << 76

    return feWord80


def qie8(feWord32, dct, iTs):
    fibCh = dct["FibCh"]

    if dct.get("CapId"):
        cap = dct["CapId"][iTs]
    elif not configuration.patterns.compressed:
        sys.exit("\n".join(["Cap-ids per time-slice not found.",
                            "Either set 'configuration.patterns.compressed = True'",
                            "or do not pass '--patterns'.",
                            ]))
    else:
        cap = 0

    qie = dct["QIE"][iTs]

    if feWord32 is None:
        feWord32 = 0

    if fibCh == 0:
        feWord32 |= qie << 25
        feWord32 |= cap << 7
    if fibCh == 1:
        feWord32 |= qie << 17
        feWord32 |= cap << 5
    if fibCh == 2:
        feWord32 |= qie << 9
        feWord32 |= cap << 3

    return feWord32


def storePatternData(d={}, utca=None):
    nFibers = configuration.hw.nFibers(utca)
    offset = 1 if configuration.patterns.rmRibbon else 0
    if not utca:
        offset += 1

    out = {}
    for iFiberPair in range(nFibers/2):
        fiber1 = 2*iFiberPair + offset
        fiber2 = 2*iFiberPair + 1 + offset
        out[fiber1] = []

        for iTs in range(configuration.patterns.nTsMax):
            feWords = []
            # Tullio says HTR f/w makes no distinction between optical cables 1 and 2
            for fiber in [fiber1, fiber2]:
                feWords.append(feWord(d, fiber, iTs))
            out[fiber1].append(patternData(feWords))
    return out


def patternData(feWords=[]):
    assert len(feWords) == 2, len(feWords)
    d = {}

    if feWords[0] is not None:
        A0 = (feWords[0] >> 24) & 0xfe
        A0 |= (feWords[0] >> 7) & 0x1
        d["A0"] = flipped(A0)

        A1 = (feWords[0] >> 17) & 0x7f
        A1 |= (feWords[0] >> 1) & 0x80
        d["A1"] = flipped(A1)

        B0 = (feWords[0] >> 8) & 0xfe
        B0 |= (feWords[0] >> 3) & 0x1
        d["B0"] = flipped(B0)

        if feWords[1] is not None:
            B1 = (feWords[1] >> 9) & 0xfe
            B1 |= (feWords[0] << 3) & 0x80
            d["B1"] = flipped(B1)

    if feWords[1] is not None:
        C0 = (feWords[1] >> 24) & 0xfe
        C0 |= (feWords[1] >> 7) & 0x1
        d["C0"] = flipped(C0)

        C1 = (feWords[1] >> 17) & 0x7f
        C1 |= (feWords[1] >> 1) & 0x80
        d["C1"] = flipped(C1)

    return d


def flipped(raw=None, nBits=8):
    out = 0
    for iBit in range(nBits):
        bit = (raw >> iBit) & 0x1
        out |= (bit << (nBits - 1 - iBit))
    return out
