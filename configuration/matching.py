# these are overwritten by oneRun.py
__okErrF = [0]
__utcaBcnDelta = 0
__utcaPipelineDelta = 0


def okErrF():
    return __okErrF


def bcnDelta(utca):
    return __utcaBcnDelta if utca else 0


def pipelineDelta(utca):
    return __utcaPipelineDelta if utca else 0
