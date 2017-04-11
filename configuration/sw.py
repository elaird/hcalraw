use_fwlite = False

def files_this_machine(run, nCyclesMax=1):
    out = []
    for stem in ["data/USC_",
                 "data/run",
                 "/tmp/USC_",
                 "/localdata/B904_Integration_",
                 "/localdata/B904_Integration_10000"]:
        for iCycle in range(nCyclesMax):
            filename = stem + "%d" % run
            if iCycle:
                filename += ".%d" % iCycle
            filename += ".root"
            out.append(filename)
    return out


def files_eos_local(run):
    stem = "root://eoscms.cern.ch//store/group/dpg_hcal/comm_hcal"
    if run < 220909:
        filename = "%s/archival/20160914_USC_Run1_runs133054-220908/USC_%d.root" % (stem, run)
    elif run < 264261:
        filename = "%s/archival/20160914_USC_LS1_runs212958-264260/USC_%d.root" % (stem, run)
    elif run < 280486:
        filename = "%s/USC/USC_%d.root" % (stem, run)
    else:
        filename = "%s/USC/run%d/USC_%d.root" % (stem, run, run)

    return [filename]


def files_xrd_global(run):
    #root://cms-xrd-global.cern.ch/
    # "dataset=/HcalNZS/Commissioning2017-v1/RAW"
    # /store/data/Commissioning2017/HcalNZS/RAW/v1/000/287/167
    # 290477
    return []


def fedMap():
    d = {"7xy": range(700, 732),
         "HO": range(724, 732),
         "HBHE": range(1100, 1118, 2),
         "HF": range(1118, 1124),
         "HC": [1134],
         "B904": [1192, 1194, 1196],
         }
    d["HBEF"] = d["HBHE"] + d["HF"]
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

    dct["Events"] = {"rawCollections": []}
    for suffix in ["rawDataCollector__LHC", "hltHcalCalibrationRaw__HLT"]:
        dct["Events"]["rawCollections"].append("FEDRawDataCollection_%s%s" % (suffix, "" if use_fwlite else ".obj"))

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
