# QIE  8: https://cms-docdb.cern.ch/cgi-bin/PublicDocDB/RetrieveFile?docid=3327&version=14&filename=HTR_MainFPGA.pdf
#         e-log post
# QIE 10: 
# QIE 11: 

import configuration, printRaw
from decode import channelId


def patterns(raw1={}, **_):
    for fedId, raw in sorted(raw1.iteritems()):
        if fedId is None:
            raw["patterns"] = True
            continue

        nFibers = configuration.hw.nFibers(raw["header"]["utca"])
        for block in raw["htrBlocks"].values():
            storePatternData(block, nFibers)

    printRaw.oneEvent(raw1)


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


def storePatternData(l={}, nFibers=None):
    offset = 1 if configuration.patterns.rmRibbon else 0

    l["patternData"] = {}
    d = l["channelData"]

    # print "Crate=%2d, Slot=%2d" % (l["Crate"], l["Slot"])
    for iFiberPair in range(nFibers/2):
        fiber1 = 2*iFiberPair + offset
        fiber2 = 2*iFiberPair + 1 + offset
        l["patternData"][fiber1] = []

        for iTs in range(configuration.patterns.nTsMax):
            feWords = []
            # Tullio says HTR f/w makes no distinction between optical cables 1 and 2
            for fiber in [fiber1, fiber2]:
                feWords.append(feWord(d, fiber, iTs))
            l["patternData"][fiber1].append(patternData(feWords))


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
