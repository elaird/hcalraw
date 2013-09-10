def nPatternFibers():
    return 6


def nPatternTs():
    return 10


def printSkip():
    return {"fibCh": [0, 2],
            "ErrF": [3],
            }


def unpackSkipFlavors(fedId=None):
    if isVme(fedId):
        return [7]
    else:
        return [4]


def bcnDelta(fedId=None):
    return 0 if isVme(fedId) else -118


def matchRange(fedId=None):
    # exceptions for Jan. 2013 slice-test (HF)
    if fedId == 990:
        return range(1, 10)
    elif fedId == 722:
        return range(9)
    else:
        return range(10)


def useEvn():
    return False

def filterEvn():
    return False

def ornTolerance():
    return 0

def printEventMap():
    return False

def identityMap():
    return False

def fiberMap():
    #return d2c()
    return {}


def isVme(fedId=None):
    return 700 <= fedId <= 731


def format(treeName="", someFedId=None):
    assert someFedId
    out = None
    if treeName == "CMSRAW":
        out = {"name":  "HCAL",
               "branch": "HCAL_DCC" if isVme(someFedId) else "Chunk",
               "auxBranch": False,
               }

    if treeName == "moltree":
        out = {"name": "MOL",
               "branch": "vec",
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
