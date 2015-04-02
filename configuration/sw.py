use_fwlite = True

def format(treeName=""):
    def __isVme(fedId=None):
        return 700 <= fedId <= 731


    dct = {"CMSRAW": {"branch": lambda fedId: "%s%d" % ("HCAL_DCC" if __isVme(fedId) else "Chunk", fedId)}}

    if use_fwlite:
        dct["Events"] = {"rawCollection": "FEDRawDataCollection_rawDataCollector__LHC", "product": True}
    else:
        dct["Events"] = {"rawCollection": "FEDRawDataCollection_rawDataCollector__LHC.obj", "product": False}

    for item in ["LuminosityBlocks", "MetaData", "ParameterSets", "Parentage", "Runs"]:
        dct[item] = None

    out = dct.get(treeName, {"branch": lambda fedId: "%d" % fedId, "skipWords64": [0, 1]})

    if out:
        if treeName == "deadbeef":
            out["nBytesPer"] = 4
            out["skipWords64"] = [0]

        if "nBytesPer" not in out:
            out["nBytesPer"] = 8

        if "skipWords64" not in out:
            out["skipWords64"] = []

    return out
