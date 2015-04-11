# these values may be overwritten by configuration.matching.pipeline_*
okErrF = [0]
__utcaBcnDelta = 0
__vmeBcnDelta = 0

# this function is overwritten by oneRun.py
def pipeline(fedId=None, slot=None, fibCh=None, utca=None):
    return 0


def bcnDelta(utca):
    return __utcaBcnDelta if utca else __vmeBcnDelta


def pipeline_LS1(fedId=None, slot=None, fibCh=None, utca=None, shiftFibCh2=None):
    """DO NOT USE THIS ONE; USE EITHER v0 or v1 BELOW"""
    """local runs; global runs before Feb. 2015"""

    assert type(shiftFibCh2) is bool

    # exceptions for Jan. 2013 slice-test (HF)
    if fedId == 990 or (fedId == 989 and 5 <= slot):
        return 1
    if fedId == 722:
        return 0

    # 1-TS shift on uHTR fibCh=2 until front f/w B_31
    if shiftFibCh2 and fibCh == 2:
        if utca:
            return 0
        else:
            return 1

    # ok
    return 0


def pipeline_v0(fedId=None, slot=None, fibCh=None, utca=None):
    global __utcaBcnDelta
    __utcaBcnDelta = -119

    global okErrF
    okErrF = [0, 1]

    return pipeline_LS1(fedId, slot, fibCh, utca, True)


def pipeline_v1(fedId=None, slot=None, fibCh=None, utca=None):
    global __utcaBcnDelta
    __utcaBcnDelta = -119

    return pipeline_LS1(fedId, slot, fibCh, utca, False)


def pipeline_v2(fedId=None, slot=None, fibCh=None, utca=None):
    """local runs; global runs from
    Feb.    2015 - Mar. 16, 2015;
    Apr. 4, 2015 - 
    """

    global __utcaBcnDelta
    __utcaBcnDelta = -131

    return 0


def pipeline_v3a(fedId=None, slot=None, fibCh=None, utca=None):
    """global runs from
    Mar. 16, 2015 - Apr. 3, 2015
    """

    global __utcaBcnDelta
    __utcaBcnDelta = -131

    return 4 if utca else 0
