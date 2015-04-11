# these values may be overwritten by configuration.matching.pipeline_*
okErrF = [0]
__utcaBcnDelta = 0
__vmeBcnDelta = 0

# this function is overwritten by oneRun.py
def pipeline(_):
    return 0


def bcnDelta(utca):
    return __utcaBcnDelta if utca else __vmeBcnDelta


def pipeline_v0(_):
    global __utcaBcnDelta
    global okErrF
    __utcaBcnDelta = -119
    okErrF = [0, 1]
    return 0


def pipeline_v1(_):
    global __utcaBcnDelta
    __utcaBcnDelta = -119
    return 0


def pipeline_v2(_):
    global __utcaBcnDelta
    __utcaBcnDelta = -131
    return 0


def pipeline_v3a(utca):
    """global runs from
    Mar. 16, 2015 - Apr. 3, 2015
    """
    global __utcaBcnDelta
    __utcaBcnDelta = -131
    return 4 if utca else 0
