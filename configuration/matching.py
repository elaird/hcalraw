# these are overwritten by oneRun.py
__ignoreCE = False
__utcaBcnDelta = 0
__utcaPipelineDelta = 0


def ignoreCE():
    return __ignoreCE


def bcnDelta(utca):
    return __utcaBcnDelta if utca else 0


def pipelineDelta(utca):
    return __utcaPipelineDelta if utca else 0
