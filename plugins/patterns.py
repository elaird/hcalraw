# QIE  8: https://cms-docdb.cern.ch/cgi-bin/PublicDocDB/RetrieveFile?docid=3327&version=14&filename=HTR_MainFPGA.pdf
# errata: http://cmsonline.cern.ch/cms-elog/807780
#
# QIE 10 (HF): https://svnweb.cern.ch/trac/cms-firmwsrc/browser/hcal/HF_RM_igloo2/trunk/docs/HF_RM_DataFormat.txt
# QIE 11 (HE): https://svnweb.cern.ch/trac/cms-firmwsrc/browser/hcal/HE_RM_igloo2/trunk/docs/HE_RM_DataFormat.txt
# QIE 11 (HB): https://svnweb.cern.ch/trac/cms-firmwsrc/browser/hcal/HB_RM_igloo2/trunk/docs/HB_RM_DataFormat.txt

import configuration.hw
import configuration.patterns


def patterns(raw1={}, **_):
    keys = [k for k in raw1.keys() if k is not None]
    for fedId in sorted(keys):
        raw = raw1[fedId]

        for iBlock, block in sorted(raw["htrBlocks"].items()):
            if block["IsTTP"]:
                continue

            # skip printer to facilitate diff
            nTsMax = raw1[None]["firstNTs"]
            header = raw["header"]
            block["patternData"] = storePatternData(block["channelData"], header["utca"], nTsMax)
            if 0 <= raw1[None]["dump"]:
                # print "Crate=%2d, Slot=%2d" % (block["Crate"], block["Slot"])
                print("\n".join(lines(header, iBlock, block, nTsMax)))


def lines(h, iBlock, block, nTsMax):
    if h["utca"]:
        moduleId = "u%2d %2d" % (block["Crate"], block["Slot"])
    else:
        moduleId = "%3d %2d" % (h["FEDid"], h["spigotList"][iBlock])

    if configuration.patterns.patternB:
        headers = [configuration.patterns.lineStart, "ModuleId", "Fibers", "Pattern"]
        chars = " ".join(["%2d" % i for i in range(nTsMax)])
        out = ["  ".join(headers + [chars])]
    else:
        out = [""]

    for fiber1, fd in sorted(block["patternData"].items()):
        out += lines_fiber_pair(fiber1, fd["flavor"], fd["patternData"], h["utca"], moduleId)

    return out


def lines_fiber_pair(fiber1, flavor, patterns, utca, moduleId):
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

        ps = patternString(flavor, patterns, key)
        if ps is None:
            continue

        if configuration.patterns.patternB:
            out.append("   ".join([descr, moduleId, fibers, "   %s" % key, "  "]) + ps)
        else:
            fiberNum = int(fibers)
            out.append("%s %2d:  %s" % (descr + moduleId, int(fibers), ps))

    return out


def patternString(flavor=None, patterns=[], key=""):
    codes = []
    for p in patterns:
        c0 = p.get(key + "0")
        c1 = p.get(key + "1")
        if c0 is None or c1 is None:
            break
        else:
            codes += [c0, c1]

    if not codes:
        return None

    if flavor in [0, 1, 3]:
        return configuration.patterns.string013(codes[0], flavor)
    elif flavor == 2:
        return configuration.patterns.string2(codes[0])
    elif 5 <= flavor <= 6:
        return configuration.patterns.string56(codes)


def feWord(d, fiber, iTs):
    word = None
    flavor = None

    for key, v in d.items():
        if v["Fiber"] != fiber:
            continue

        if v.get("LE"):  # 8b/10b errors
            continue

        if len(v["QIE"]) <= iTs:
            continue

        flavor = v["Flavor"]
        if 0 <= flavor <= 1:
            word = fe_word_qie11e(word, v, iTs)
        elif flavor == 2:
            word = fe_word_qie10(word, v, iTs)
        elif flavor == 3:
            word = fe_word_qie11b(word, v, iTs)
        elif 5 <= flavor <= 6:
            word = fe_word_qie8(word, v, iTs)

    return flavor, word


def fe_word_qie11b(feWord88, dct, iTs):
    if feWord88 is None:
        feWord88 = 0

    # FIXME: add missing bits:
    # Byte1  = isAnyTDC61, isAnyTDC60, isAnyTDC59, isAnyTDC58, 2-bit consensus_CapID, CapEr, Available (formerly BC0)

    iByteQ = 8 * (1 + dct["FibCh"])
    feWord88 |= (dct["QIE"][iTs] & 0xff) << iByteQ
    iByteT = 72 + 2 * dct["FibCh"]
    feWord88 |= (dct["TDC"][iTs] & 0x3 ) << iByteT
    return feWord88


def fe_word_qie11e(feWord88, dct, iTs):
    if feWord88 is None:
        feWord88 = 0

    # FIXME: add missing 4 bits
    # Byte1  = {LE_TDC0[3:0], 2-bit consensus_CapID, CapEr, BC0};

    if dct["FibCh"] == 0:
        feWord88 |= ((dct["TDC"][iTs] >> 0) &  0xf ) <<  4
        feWord88 |= ( dct["QIE"][iTs]       & 0xff ) <<  8
        feWord88 |= ((dct["TDC"][iTs] >> 4) &  0x3 ) << 56
    elif dct["FibCh"] == 1:
        feWord88 |= ( dct["QIE"][iTs]       & 0xff ) << 16
        feWord88 |= ((dct["TDC"][iTs] >> 0) & 0x3f ) << 58
    elif dct["FibCh"] == 2:
        feWord88 |= ( dct["QIE"][iTs]       & 0xff ) << 24
        feWord88 |= ((dct["TDC"][iTs] >> 0) & 0x3f ) << 64
    elif dct["FibCh"] == 3:
        feWord88 |= ( dct["QIE"][iTs]       & 0xff ) << 32
        feWord88 |= ((dct["TDC"][iTs] >> 0) & 0x3f ) << 70
    elif dct["FibCh"] == 4:
        feWord88 |= ( dct["QIE"][iTs]       & 0xff ) << 40
        feWord88 |= ((dct["TDC"][iTs] >> 0) & 0x3f ) << 76
    elif dct["FibCh"] == 5:
        feWord88 |= ( dct["QIE"][iTs]       & 0xff ) << 48
        feWord88 |= ((dct["TDC"][iTs] >> 0) & 0x3f ) << 82

    return feWord88


def fe_word_qie10(feWord80, dct, iTs):
    if feWord80 is None:
        feWord80 = 0

    if dct["FibCh"] == 0:
        feWord80 |= ( dct["TDC_TE"][iTs]    &  0xf ) <<  0
        feWord80 |= ( dct["CapId"][iTs]     &  0x3 ) <<  8
        feWord80 |= ( dct["QIE"][iTs]       & 0xff ) << 16
        feWord80 |= ((dct["TDC"][iTs] >> 4) &  0x3 ) << 48
        feWord80 |= ((dct["TDC"][iTs] >> 2) &  0x3 ) << 56
        feWord80 |= ((dct["TDC"][iTs] >> 0) &  0x3 ) << 64
        feWord80 |= ((dct["TDC_TE"][iTs]>>4)&  0x1 ) << 80
    elif dct["FibCh"] == 1:
        feWord80 |= ( dct["TDC_TE"][iTs]    &  0xf ) <<  4
        feWord80 |= ( dct["CapId"][iTs]     &  0x3 ) << 10
        feWord80 |= ( dct["QIE"][iTs]       & 0xff ) << 24
        feWord80 |= ((dct["TDC"][iTs] >> 4) &  0x3 ) << 50
        feWord80 |= ((dct["TDC"][iTs] >> 2) &  0x3 ) << 58
        feWord80 |= ((dct["TDC"][iTs] >> 0) &  0x3 ) << 66
        feWord80 |= ((dct["TDC_TE"][iTs]>>4)&  0x1 ) << 81
    elif dct["FibCh"] == 2:
        feWord80 |= ( dct["CapId"][iTs]     &  0x3 ) << 12
        feWord80 |= ( dct["QIE"][iTs]       & 0xff ) << 32
        feWord80 |= ((dct["TDC"][iTs] >> 4) &  0x3 ) << 52
        feWord80 |= ((dct["TDC"][iTs] >> 2) &  0x3 ) << 60
        feWord80 |= ((dct["TDC"][iTs] >> 0) &  0x3 ) << 68
        feWord80 |= ( dct["TDC_TE"][iTs]    &  0xf ) << 72
        feWord80 |= ((dct["TDC_TE"][iTs]>>4)&  0x1 ) << 82
    elif dct["FibCh"] == 3:
        feWord80 |= ( dct["CapId"][iTs]     &  0x3 ) << 14
        feWord80 |= ( dct["QIE"][iTs]       & 0xff ) << 40
        feWord80 |= ((dct["TDC"][iTs] >> 4) &  0x3 ) << 54
        feWord80 |= ((dct["TDC"][iTs] >> 2) &  0x3 ) << 62
        feWord80 |= ((dct["TDC"][iTs] >> 0) &  0x3 ) << 70
        feWord80 |= ( dct["TDC_TE"][iTs]    &  0xf ) << 76
        feWord80 |= ((dct["TDC_TE"][iTs]>>4)&  0x1 ) << 83

    return feWord80


def fe_word_qie8(feWord32, dct, iTs):
    capids = dct.get("CapId", [])
    if iTs < len(capids):
        cap = capids[iTs]
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

    if dct["FibCh"] == 0:
        feWord32 |= qie << 25
        feWord32 |= cap << 7
    elif dct["FibCh"] == 1:
        feWord32 |= qie << 17
        feWord32 |= cap << 5
    elif dct["FibCh"] == 2:
        feWord32 |= qie << 9
        feWord32 |= cap << 3

    return feWord32


def storePatternData(d={}, utca=None, nTsMax=None):
    offset = 0
    if not utca:
        offset += 1
    if configuration.patterns.rmRibbon:
        offset += 1

    out = {}
    for iFiberPair in range(configuration.hw.nFibers(utca) // 2):
        fiber1 = 2*iFiberPair + offset
        out[fiber1] = {"flavor": None,
                       "patternData": [],
                       }

        for iTs in range(nTsMax):
            feWords = []
            flavors = []
            # Tullio says HTR f/w makes no distinction between optical cables 1 and 2
            for fiber in [fiber1, 1 + fiber1]:
                flavor, word = feWord(d, fiber, iTs)
                flavors.append(flavor)
                feWords.append(word)

            flavors = [x for x in set(flavors) if x is not None]
            assert (len(flavors) <= 1) or set(flavors) == set([0, 1]) or set(flavors) == set([5, 6]), flavors

            pd = None
            if not flavors:
                continue

            # for flavors 0-3, all time slices have the same pattern; use TS1
            if 0 <= flavors[0] <= 3 and iTs == 1:
                pd = pattern_data_qie1x(feWords)
            elif 5 <= flavors[0] <= 6:
                pd = pattern_data_qie8(feWords)

            if pd is not None:
                out[fiber1]["flavor"] = flavors[0]
                out[fiber1]["patternData"].append(pd)

    return out


def pattern_data_qie1x(feWords):
    assert len(feWords) == 2, len(feWords)
    d = {}
    # print feWords
    if feWords[0] is not None:
        d["A0"] = feWords[0]
        d["A1"] = 0

    if feWords[1] is not None:
        d["C0"] = feWords[1]
        d["C1"] = 0

    return d


def pattern_data_qie8(feWords=[]):
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
