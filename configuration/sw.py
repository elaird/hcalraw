use_fwlite = False
eosprefix = "root://eoscms.cern.ch/"
#root://cms-xrd-global.cern.ch/

def fedMap():
    d = {"vHBHE": range(700, 718),
         "vHF": range(718, 724),
         "HO": range(724, 732),
         "HBHE": range(1100, 1118, 2),
         "HF": range(1118, 1124),
         "HC": [1132, 1134],
         }

    d["vHCAL"] = d["vHBHE"] + d["vHF"] + d["HO"]
    d["uHCAL"] = d["HBHE"] + d["HF"] + d["HC"]
    d["HCAL"] = d["HBHE"] + d["HF"] + d["HO"] + d["HC"]
    return d


def fedList(s=""):
    d = fedMap()
    if not s:
        return []
    if s in d:
        return d[s]

    out = [int(x) for x in s.split(",")]
    return out


def format(treeName=""):
    def __isVme(fedId=None):
        return 700 <= fedId <= 731


    dct = {"CMSRAW": {"branch": lambda fedId: "%s%03d" % ("HCAL_DCC" if __isVme(fedId) else "Chunk", fedId)}}

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
