import re


__pattern = re.compile('-  H .. .. .. .. .. .. ..  -')

# these are overwritten by oneRun.py
matchRange = lambda x, **_: []
__utcaBcnDelta = None
__compressedPatterns = None
__asciifyPatterns = None
__regMatchPatterns = None


def patternString(codes=[]):
    if not any(codes):
        return None

    l = []
    for code in codes:
        if __compressedPatterns:
            code = (code >> 1) & 0x3f
            code += 32

        if __asciifyPatterns and (32 <= code <= 126):
            l.append("%2s" % chr(code))
        else:
            l.append("%2x" % code)

    s = " ".join(l)
    match = __pattern.search(s)
    if __regMatchPatterns and match:
        m = match.group()
        m = m.replace(" ", "").replace("-", "")
        return "%s %s %s" % (m[:-2].ljust(6), m[-2], m[-1])
    else:
        return s


def bcnDelta(utca):
    return __utcaBcnDelta if utca else 0


def nFibers(utca):
    return 24 if utca else 8


def unpackSkipFlavors(utca):
    return [7]


def fedMap():
    d = {"HBHE": range(700, 718),
         "HF": range(718, 724),
         "HO": range(724, 732),
         "uHF": [1118, 1120, 1122],
         }

    d["HBHEHF"] = d["HBHE"] + d["HF"]
    d["HBEF"] = d["HBHEHF"]
    d["HCAL"] = d["HBEF"] + d["HO"]
    d["uHCAL"] = d["HCAL"] + d["uHF"]
    return d


def rbxes():
    hbef = range(1, 19)
    ho   = range(1, 13)
    ho12 = range(2, 14, 2)

    out = []
    for subdet, lst in [("HBM",  hbef),
                        ("HBP",  hbef),
                        ("HEM",  hbef),
                        ("HEP",  hbef),
                        ("HFM",  hbef),
                        ("HFP",  hbef),
                        ("HO2M", ho12),
                        ("HO1M", ho12),
                        ("HO0",  ho  ),
                        ("HO1P", ho12),
                        ("HO2P", ho12),
                        ]:
        for i in lst:
            out.append("%s%02d" % (subdet, i))
    return out


def matchRange_LS1(fedId=None, slot=None, fibCh=None, utca=None, shiftFibCh2=None):
    """DO NOT USE THIS ONE; USE EITHER v0 or v1 BELOW"""
    """local runs; global runs before Feb. 2015"""

    assert type(shiftFibCh2) is bool

    # exceptions for Jan. 2013 slice-test (HF)
    if fedId == 990 or (fedId == 989 and 5 <= slot):
        return range(1, 10)
    if fedId == 722:
        return range(9)

    # 1-TS shift on uHTR fibCh=2 until front f/w B_31
    if shiftFibCh2 and fibCh == 2:
        if utca:
            return range(9)
        else:
            return range(1, 10)

    # ok
    return range(10)


def matchRange_v0(fedId=None, slot=None, fibCh=None, utca=None):
    return matchRange_LS1(fedId, slot, fibCh, utca, True)


def matchRange_v1(fedId=None, slot=None, fibCh=None, utca=None):
    return matchRange_LS1(fedId, slot, fibCh, utca, False)


def matchRange_v2(fedId=None, slot=None, fibCh=None, utca=None):
    """global runs during/since Feb. 2015"""

    if 1100 <= fedId:
        return range(2, 8)
    else:
        return range(6)


def fiberMap(fedId=None):
    if 989 <= fedId <= 990:  # mCTR2d
        return d2c()
    else:
        return {}


def expectedHtr(fedId, spigot):
    slot = spigot/2 + (13 if (fedId % 2) else 2)
    if slot == 19:  # DCC occupies slots 19-20
        slot = 21
    return {"Top": {1: "t", 0: "b"}[1 - (spigot % 2)],
            "Slot": slot}


def format(treeName=""):
    def _isVme(fedId=None):
        return 700 <= fedId <= 731

    out = None
    if treeName == "CMSRAW":
        out = {"name":  "HCAL",
               "branch": lambda fedId: "%s%d" % ("HCAL_DCC" if _isVme(fedId) else "Chunk", fedId),
               "auxBranch": False,
               }

    if treeName == "moltree":
        out = {"name": "MOL",
               "branch": lambda fedId: "vec%d" % fedId,
               }

    if treeName == "deadbeeftree":
        out = {"name": "DB",
               "branch": lambda fedId: "db%d" % fedId,
               }

    if treeName == "Events":
        out = {"name": "CMS",
               "auxBranch": True,
               "rawCollection": "FEDRawDataCollection_rawDataCollector__LHC",
               }
    if out:
        out["treeName"] = treeName
    return out


def d2c():
    return {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
            7:   9,
            8:  11,
            9:  12,
            10: 10,
            11:  8,
            12:  7,
            }
