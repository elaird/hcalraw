# these value may be overwritten by configuration.matching.tsRange_*
okErrF = [0]
__utcaBcnDelta = 0
__vmeBcnDelta = 0

# this function is overwritten by oneRun.py
def tsRange(fedId=None, slot=None, fibCh=None, utca=None):
    return []


def bcnDelta(utca):
    return __utcaBcnDelta if utca else __vmeBcnDelta


def tsRange_LS1(fedId=None, slot=None, fibCh=None, utca=None, shiftFibCh2=None):
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


def tsRange_v0(fedId=None, slot=None, fibCh=None, utca=None):
    global __utcaBcnDelta
    __utcaBcnDelta = -119

    global okErrF
    okErrF = [0, 1]

    return tsRange_LS1(fedId, slot, fibCh, utca, True)


def tsRange_v1(fedId=None, slot=None, fibCh=None, utca=None):
    global __utcaBcnDelta
    __utcaBcnDelta = -119

    return tsRange_LS1(fedId, slot, fibCh, utca, False)


def tsRange_v2(fedId=None, slot=None, fibCh=None, utca=None):
    global __utcaBcnDelta
    __utcaBcnDelta = -131

    return tsRange_LS1(fedId, slot, fibCh, utca, False)


def tsRange_v3(fedId=None, slot=None, fibCh=None, utca=None):
    """global runs from Feb. 2015 - Mar. 16, 2015"""

    global __utcaBcnDelta
    __utcaBcnDelta = -131

    if 1100 <= fedId:
        return range(2, 8)
    else:
        return range(6)


def tsRange_v4(fedId=None, slot=None, fibCh=None, utca=None):
    """global runs from March 16, 2015"""

    global __utcaBcnDelta
    __utcaBcnDelta = -131

    return range(6)


def tsRange_v4a(fedId=None, slot=None, fibCh=None, utca=None):
    """hack"""

    global __utcaBcnDelta
    __utcaBcnDelta = -131

    if fed < 1000:
        return [0, 1]
    else:
        return [4, 5]
