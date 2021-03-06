import printer

use_fwlite = False

def files_this_machine(run, nCyclesMax=1):
    out = []
    for stem in ["data/USC_",
                 "data/run",
                 "data/FNAL_",
                 "/tmp/USC_",
                 "/hcal_depot1/data/USC_",
                 "data/B904_Integration_",
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
    elif 100000000 < run:
        filename = "%s/B904/run%d/B904_Integration_%d.root" % (stem, run, run)
    else:
        filename = "%s/USC/run%d/USC_%d.root" % (stem, run, run)

    return [filename]


def dirs_global(run):
    #root://cms-xrd-global.cern.ch/
    # prefix = "root://eoscms.cern.ch/"
    prefix = ""
    midfix = "000/%03d/%03d" % (run // 1000, run % 1000)
    minidaq = "%s/eos/cms/store/t0streamer/Minidaq/A/%s/" % (prefix, midfix)

    out = []
    for era in ["Commissioning2020"]:
        for subdir in ["HcalNZS/RAW/v1", "MinimumBias/RAW/v1", "TestEnablesEcalHcal/RAW/Express-v1"]:
            out.append("%s/eos/cms/store/data/%s/%s/%s/00000/" % (prefix, era, subdir, midfix))
    return out


def crateList(usc=True):
    h = set(range(20, 39)) - set([28, 33, 36])
    if usc:
        return list(h)
    else:  # B904
        return [50, 51, 52, 53, 61, 62, 63]


def set_default_feds1(options):
    if options.feds1 == "HCAL":
        if "B904" in options.file1:
            options.feds1 = "B904"
        elif "FNAL" in options.file1:
            options.feds1 = "WH14"


def fedMap():
    d = {"0xy": list(range(60, 74)),
         "7xy": list(range(700, 732)),
         "HO": [1124, 1125, 1126, 1127, 1128, 1129, 1134, 1135],
         "HBHE": list(range(1100, 1118)),
         "HF": list(range(1118, 1124)),
         "B904": list(range(1180, 1188)) + list(range(1192, 1198)),
         "WH14": [1776],
         }
    d["HCAL"] = d["HBHE"] + d["HF"] + d["HO"]
    return d


def fedList(s):
    out = []

    if not s:
        return out

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
    return 60 <= fedId <= 73


def format(treeName=""):
    def __branch(fedId):
        if fedId == 1:
            return "HCAL_Trigger"
        if 700 <= fedId <= 731:
            return "HCAL_DCC%03d" % fedId
        return "Chunk%03d" % fedId

    dct = {"CMSRAW": {"branch": __branch}}

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
