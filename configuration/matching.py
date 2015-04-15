okErrF = [0]             # set to [0, 1] for some test runs from 2013 - 2014
__utcaBcnDelta = 0       # this is overwritten by oneRun.py
__utcaPipelineDelta = 0  # this is overwritten by oneRun.py


def bcnDelta(utca):
    return __utcaBcnDelta if utca else 0


def pipelineDelta(utca):
    return __utcaPipelineDelta if utca else 0
