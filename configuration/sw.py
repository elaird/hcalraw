import printer

use_fwlite = False

def files_this_machine(run, nCyclesMax=1):
    out = []
    for stem in ["data/USC_",
                 "data/run",
                 "data/FNAL_",
                 "/tmp/USC_",
                 "/hcaldepot1/data/USC_",
                 "data/B904_Integration_0000",
                 "data/B904_Integration_10000",
                 "/localdata/B904_Integration_",
                 "/localdata/B904_Integration_10000"]:
        for iCycle in range(nCyclesMax):
            if "FNAL" in stem:
                filename = stem + "%06d" % run  # FNAL runs might be less than 100000
            else:
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


def dirs_global(run):
    #root://cms-xrd-global.cern.ch/
    # prefix = "root://eoscms.cern.ch/"
    prefix = ""
    midfix = "000/%03d/%03d" % (run/1000, run % 1000)
    minidaq = "%s/eos/cms/store/t0streamer/Minidaq/A/%s/" % (prefix, midfix)

    out = []
    for era in ["Commissioning2018"]:
        for subdir in ["HcalNZS/RAW/v1", "MinimumBias/RAW/v1", "TestEnablesEcalHcal/RAW/Express-v1"]:
            out.append("%s/eos/cms/store/data/%s/%s/%s/00000/" % (prefix, era, subdir, midfix))
    return out


def crateList(usc=True):
    h = []
    for crate in [3, 6, 7, 13] + range(20, 39): # USC
        if crate in [23, 26, 27, 33] + [28, 36]:  # uHO + do not exist
            continue
        h.append(crate)
    if usc:
        return h
    else:  # B904
        return [50, 51, 52, 53, 61, 62, 63]


def set_default_feds1(options):
    if options.feds1 == "HCAL":
        if "B904" in options.file1:
            options.feds1 = "B904"
        elif "FNAL" in options.file1:
            options.feds1 = "WH14"


def fedMap():
    d = {"0xy": range(60, 73),
         "7xy": range(700, 732),
         "HO": range(724, 732),
         "HBHE": range(1100, 1118),
         "HF": range(1118, 1124),
         "HC": [1134, 1135],
         "B904": range(1180, 1188) + [1192, 1194, 1196],
         "WH14": [1776],
         }
    d["HBEF"] = d["HBHE"] + d["HF"]
    d["HCAL"] = d["HBHE"] + d["HF"] + d["HO"] + d["HC"]
    return d


def fedList(s=""):
    out = []

    d = fedMap()
    for x in s.split(","):
        if not x:
            continue

        y = d.get(x)
        if y is None:
            try:
                y = int(x)
                out.append(y)
            except ValueError:
                printer.warning("Could not convert '%s' to an integer" % x)
        else:
            out += y

    return out


def histo_fed(fedId):
    return 60 <= fedId <= 72


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
