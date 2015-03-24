import re


pattern = re.compile('-  H .. .. .. .. .. .. ..  -')
compressedPatterns = True

# these value may be overwritten by configuration.matchRange_*
__utcaBcnDelta = 0
__vmeBcnDelta = 0

# this function is overwritten by oneRun.py
def matchRange(fedId=None, slot=None, fibCh=None, utca=None):
    return []


def patternString(codes=[], asciifyPatterns=True, regMatchPatterns=True):
    if not any(codes):
        return None

    l = []
    for code in codes:
        if compressedPatterns:
            code = (code >> 1) & 0x3f
            code += 32

        if asciifyPatterns and (32 <= code <= 126):
            l.append("%2s" % chr(code))
        else:
            l.append("%2x" % code)

    s = " ".join(l)
    match = pattern.search(s)
    if regMatchPatterns and match:
        m = match.group()
        m = m.replace(" ", "").replace("-", "")
        return "%s %s %s" % (m[:-2].ljust(6), m[-2], m[-1])
    else:
        return s


def bcnDelta(utca):
    return __utcaBcnDelta if utca else __vmeBcnDelta


def nFibers(utca):
    return 24 if utca else 8


def flavorLabels():
    return {4: "utp",
            5: "cpt",
            6: "vrb",
            7: "tch",
            }


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
    hbe  = range(1, 19)
    hfo  = range(1, 13)
    ho12 = range(2, 14, 2)

    out = []
    for subdet, lst in [("HBM",  hbe),
                        ("HBP",  hbe),
                        ("HEM",  hbe),
                        ("HEP",  hbe),
                        ("HFM",  hfo),
                        ("HFP",  hfo),
                        ("HO2M", ho12),
                        ("HO1M", ho12),
                        ("HO0",  hfo ),
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

    global __utcaBcnDelta
    __utcaBcnDelta = -119

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
    """global runs from Feb. 2015 - Mar. 16, 2015"""

    global __utcaBcnDelta
    __utcaBcnDelta = -131

    if 1100 <= fedId:
        return range(2, 8)
    else:
        return range(6)


def matchRange_v3(fedId=None, slot=None, fibCh=None, utca=None):
    """global runs from March 16, 2015"""

    global __utcaBcnDelta
    __utcaBcnDelta = -131

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


def __isVme(fedId=None):
    return 700 <= fedId <= 731


def expectedCrate(fedId):
    # http://cmsdoc.cern.ch/cms/HCAL/document/CountingHouse/Crates/VME_interfaces_newPCs.htm
    if not __isVme(fedId):
        return -1

    return {350:  4,
            351:  0,
            352:  1,
            353:  5,
            354: 11,
            355: 15,
            356: 17,
            357: 14,
            358: 10,
            359:  2,
            360:  9,
            361: 12,
            362:  3,
            363:  7,
            364:  6,
            365: 13}[fedId/2]


def transformed_crate_slot(crate, slot):
    slot2 = None
    if crate < 20:
        # VME --> uTCA
        crate2 = crate + 20

        if 2 <= slot <= 7:
            slot2 = slot - 1
        elif 13 <= slot <= 18:
            slot2 = slot - 6
    else:
        # uTCA --> VME
        crate2 = crate - 20
        if slot <= 6:
            slot2 = 1 + slot
        elif 7 <= slot <= 12:
            slot2 = 6 + slot
    return (crate2, slot2)


def transformed_qie(crate, slot, top, fiber, fibCh):
    crate2, slot2 = transformed_crate_slot(crate, slot)
    if slot2 is None:
        return None

    if crate < 20:
        # VME --> uTCA
        top2 = " "
        fiber2 = fiber + 1
        if top == "t":
            fiber2 += 12
    else:
        # uTCA --> VME
        fiber2 = fiber - 1
        if 12 <= fiber2:
            fiber2 -= 12
            top2 = "t"
        else:
            top2 = "b"

    return (crate2, slot2, top2, fiber2, fibCh)


def transformed_tp(crate, slot, top, key):
    crate2, slot2 = transformed_crate_slot(crate, slot)
    if slot2 is None:
        return None

    if type(key) is tuple and len(key) == 2 and key[0] == 6:  # VME
        top2 = " "
        slb, ch = key
        if top == "b":
            ch -= 2
        if slot in [2, 4, 6, 13, 15, 17]:
            ch -= 2
        key2 = 0xc0 + ch
    else:
        return None

    return (crate2, slot2, top2, key2)


def format(treeName=""):
    out = None
    if treeName == "CMSRAW":
        out = {"name":  "HCAL",
               "branch": lambda fedId: "%s%d" % ("HCAL_DCC" if __isVme(fedId) else "Chunk", fedId),
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
               "auxBranch": False,
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
