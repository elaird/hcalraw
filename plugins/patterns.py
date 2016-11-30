# QIE  8: https://cms-docdb.cern.ch/cgi-bin/PublicDocDB/RetrieveFile?docid=3327&version=14&filename=HTR_MainFPGA.pdf
#         e-log post
# QIE 10: 
# QIE 11: 

import configuration.hw
import configuration.patterns
from printRaw import spigotList
from decode import channelId


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
    patternB = configuration.patterns.patternB
    descr = configuration.patterns.lineStart

    if h["utca"]:
        moduleId = "u%2d %2d" % (block["Crate"], block["Slot"])
    else:
        moduleId = "%3d %2d" % (h["FEDid"], spigotList(h)[iBlock])

    if patternB:
        headers = [descr, "ModuleId", "Fibers", "Pattern"]
        chars = " ".join(["%2d" % i for i in range(20)])
        out = ["  ".join(headers+[chars])]
    else:
        out = [""]

    d = storePatternData(block["channelData"],
                         configuration.hw.nFibers(h["utca"])
                         )

    for fiber1, lst in sorted(d.iteritems()):
        out += lines_one_fiber(fiber1, lst, h["utca"], moduleId, patternB, descr)
    return out


def lines_one_fiber(fiber1, lst, utca, moduleId, patternB, descr):
    out = []
    for key in ["A", "B", "C"]:
        if (not patternB) and key == "B":
            continue

        fiber1_ = fiber1 + (0 if utca else 1)
        if key == "B":
            fibers = "  %2d,%2d" % (fiber1_, 1 + fiber1_)
        elif key == "A":
            fibers = "     %2d" % (fiber1_)
        elif key == "C":
            fibers = "     %2d" % (1 + fiber1_)

        ps = patternString(lst, key)
        if ps is None:
            continue

        if patternB:
            out.append("   ".join([descr + moduleId, fibers, "  %s" % key, "  "]) + ps)
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
    feWord32 = None
    for fibCh in range(configuration.patterns.nFibChMax):
        key = channelId(fiber, fibCh)
        if key not in d:
            continue

        if d[key]["ErrF"] == 3:  # 8b/10b errors
            continue

        qies = d[key]["QIE"]
        if len(qies) <= iTs:
            continue

        flavor = d[key]["Flavor"]
        if 5 <= flavor <= 6:
            qie = qies[iTs]
            if d[key].get("CapId"):
                cap = d[key]["CapId"][iTs]
            elif not configuration.patterns.compressed:
                sys.exit("\n".join(["Cap-ids per time-slice not found.",
                                    "Either set 'configuration.patterns.compressed = True'",
                                    "or do not pass '--patterns'.",
                                    ]))
            else:
                cap = 0

            if (feWord32 is None) and (0 <= fibCh <= 2):
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
        elif 0 <= flavor <= 1:
            pass
        elif flavor == 2:
            pass

    return feWord32


def storePatternData(d={}, nFibers=None):
    offset = 1 if configuration.patterns.rmRibbon else 0

    out = {}

    # print "Crate=%2d, Slot=%2d" % (l["Crate"], l["Slot"])
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
