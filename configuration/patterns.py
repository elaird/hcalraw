import re


patternB = False           # consider also patterns mixed across fibers
rmRibbon = False           # pair central 6 fibers (of 8 or 12)
compressed = True          # handle lack of per-TS capids
lineStart = "pattern on "  # print with pattern; used by diff.py

pattern = re.compile('-  H .. .. .. .. .. .. ..  -')


def string(codes=[], asciifyPatterns=True, regMatchPatterns=True):
    if not any(codes):
        return None

    l = []
    for code in codes:
        if compressed:
            code = (code >> 1) & 0x3f
            code += 32

        if asciifyPatterns and (32 <= code <= 126):
            l.append("%2s" % chr(code))
        else:
            l.append("%2x" % code)

    s = " ".join(l)
    match = pattern.search(s)
    if regMatchPatterns and match:
        m = match.group()
        m = m.replace(" ", "").replace("-", "")
        return "%s %s %s" % (m[:-2].ljust(6), m[-2], m[-1])
    else:
        return s


def rbxes():
    hbe  = range(1, 19)
    hfo  = range(1, 13)
    ho12 = range(2, 14, 2)

    out = []
    for subdet, lst in [("HBM",  hbe),
                        ("HBP",  hbe),
                        ("HEM",  hbe),
                        ("HEP",  hbe),
                        ("HFM",  hfo),
                        ("HFP",  hfo),
                        ("HO2M", ho12),
                        ("HO1M", ho12),
                        ("HO0",  hfo ),
                        ("HO1P", ho12),
                        ("HO2P", ho12),
                        ]:
        for i in lst:
            out.append("%s%02d" % (subdet, i))
    return out


def expectedHtr(fedId, spigot):
    slot = spigot/2 + (13 if (fedId % 2) else 2)
    if slot == 19:  # DCC occupies slots 19-20
        slot = 21
    return {"Top": {1: "t", 0: "b"}[1 - (spigot % 2)],
            "Slot": slot}


def expectedCrate(fedId):
    # http://cmsdoc.cern.ch/cms/HCAL/document/CountingHouse/Crates/VME_interfaces_newPCs.htm
    return {350:  4,
            351:  0,
            352:  1,
            353:  5,
            354: 11,
            355: 15,
            356: 17,
            357: 14,
            358: 10,
            359:  2,
            360:  9,
            361: 12,
            362:  3,
            363:  7,
            364:  6,
            365: 13}.get(fedId / 2, -1)
