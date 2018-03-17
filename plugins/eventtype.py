# from https://gitlab.cern.ch/cmshcos/hcal/blob/integration/hcalBase/include/hcal/toolbox/OrbitGapOperations.hh
#                   -1,      0,          1,        ..., hfraddamph8 = 22
# SetupType = ["unknown", "null", "pedestal", "hfraddam", "hbhehpd", "ho", "hf", "zdc", "hepmega", "hemmega", "hbpmega", "hbmmega", "", "crf", "calib", "safe", "hfraddamph1", "hfraddamph2", "hfraddamph3", "hfraddamph4", "hfraddamph5", "hfraddamph6", "hfraddamph7", "hfraddamph8"]
#                   -1,      0,          1,        ..., hfraddam = 15
SetupType = ["unknown", "null", "pedestal", "hfraddam", "hbhehpd", "ho", "hf", "zdc", "hepmega", "hemmega", "hbpmega", "hbmmega", "", "crf", "calib", "safe", "hfrad*"]


def eventtype(raw1={}, fedId=1135, keepType=15, userKey=16, userValue=None, **_):
    raw = raw1.get(fedId)
    if not raw:
        return True

    for iBlock, block in sorted(raw["htrBlocks"].iteritems()):
        if block["IsIO"] and block["EventType"] == keepType:
            if userValue is not None and block["UserWords"].get(userKey) != userValue:
                continue
            return

    return True
