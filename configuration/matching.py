okErrF = [0]        # set to [0, 1] for some test runs from 2013 - 2014
__utcaBcnDelta = 0  # this is overwritten by oneRun.py


def bcnDelta(utca):
    return __utcaBcnDelta if utca else 0


def pipelineDelta(utca):
    ###################################################
    ## global runs from Mar. 16, 2015 - Apr. 3, 2015 ##
    #                                                 #
    # return 4 if utca else 0                         #
    ###################################################
    return 0
