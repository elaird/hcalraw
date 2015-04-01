import re


use_fwlite = True

# these value may be overwritten by configuration.matchRange_*
matchSkipErrF = [1, 3]
__utcaBcnDelta = 0
__vmeBcnDelta = 0

# this function is overwritten by oneRun.py
def matchRange(fedId=None, slot=None, fibCh=None, utca=None):
    return []


def bcnDelta(utca):
    return __utcaBcnDelta if utca else __vmeBcnDelta


def nFibers(utca):
    return 24 if utca else 8


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


def fedList(s=""):
    d = fedMap()
    if not s:
        return []
    if s in d:
        return d[s]

    out = [int(x) for x in s.split(",")]
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
    global __utcaBcnDelta
    __utcaBcnDelta = -119

    global matchSkipErrF
    matchSkipErrF = [3]

    return matchRange_LS1(fedId, slot, fibCh, utca, True)


def matchRange_v1(fedId=None, slot=None, fibCh=None, utca=None):
    global __utcaBcnDelta
    __utcaBcnDelta = -119

    return matchRange_LS1(fedId, slot, fibCh, utca, False)


def matchRange_v2(fedId=None, slot=None, fibCh=None, utca=None):
    global __utcaBcnDelta
    __utcaBcnDelta = -131

    return matchRange_LS1(fedId, slot, fibCh, utca, False)


def matchRange_v3(fedId=None, slot=None, fibCh=None, utca=None):
    """global runs from Feb. 2015 - Mar. 16, 2015"""

    global __utcaBcnDelta
    __utcaBcnDelta = -131

    if 1100 <= fedId:
        return range(2, 8)
    else:
        return range(6)


def matchRange_v4(fedId=None, slot=None, fibCh=None, utca=None):
    """global runs from March 16, 2015"""

    global __utcaBcnDelta
    __utcaBcnDelta = -131

    return range(6)


def matchRange_v4a(fedId=None, slot=None, fibCh=None, utca=None):
    """hack"""

    global __utcaBcnDelta
    __utcaBcnDelta = -131

    if __isVme(fedId):
        return [0, 1]
    else:
        return [4, 5]


def fiberMap(fedId=None):
    if 989 <= fedId <= 990:  # mCTR2d
        return d2c()
    else:
        return {}


def __isVme(fedId=None):
    return 700 <= fedId <= 731


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
    dct = {"CMSRAW": {"branch": lambda fedId: "%s%d" % ("HCAL_DCC" if __isVme(fedId) else "Chunk", fedId)}}

    if use_fwlite:
        dct["Events"] = {"rawCollection": "FEDRawDataCollection_rawDataCollector__LHC", "product": True}
    else:
        dct["Events"] = {"rawCollection": "FEDRawDataCollection_rawDataCollector__LHC.obj", "product": False}

    for item in ["LuminosityBlocks", "MetaData", "ParameterSets", "Parentage", "Runs"]:
        dct[item] = None
    out = dct.get(treeName, {"branch": lambda fedId: "%d" % fedId})
    if out:
        out["nBytesPer"] = 4 if treeName == "deadbeef" else 8
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
