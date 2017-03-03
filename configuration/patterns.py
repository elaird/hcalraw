import re

nTsMax = 20                # consider up to this many acquired time slices (phase-0)
patternB = False           # consider also patterns mixed across fibers
rmRibbon = False           # pair central 6 fibers (of 8 or 12)
compressed = True          # handle lack of per-TS capids
lineStart = "pattern on "  # print with pattern; used by diff.py

# must match settings used to generate patterns
ngOffset = 16              # number of bits by which to shift ngFiberID
pattern = re.compile('-  H .. .. .. .. .. .. ..  -')


def prefix_side_number(rbx):
    rbxname_pattern = re.compile('([A-Z]*)([0-9]*)')
    match = rbxname_pattern.search(rbx)
    prefix = match.group(1)
    if prefix.endswith("M") or prefix.endswith("P"):
        side = prefix[-1]
        prefix = prefix[:-1]
    else:
        side = ""
    return prefix, side, int(match.group(2))


def subdetector_code(rbx_prefix):
    # https://github.com/cms-sw/cmssw/blob/CMSSW_9_0_X/DataFormats/HcalDetId/interface/HcalSubdetector.h
    # enum HcalSubdetector { HcalEmpty=0, HcalBarrel=1, HcalEndcap=2, HcalOuter=3, HcalForward=4, HcalTriggerTower=5, HcalOther=7 };
    return {"HB": 1,
            "HE": 2,
            "HO": 3,
            "HF": 4,
            }.get(rbx_prefix, 7)


def side_code(rbx_side):
    return {"": 0,
            "M": 1,
            "P": 2,
            }.get(rbx_side, 7)


def decoded_link(code):
    link_num = (code >> 81) & 0x3
    top = (code >> 83) & 0x1
    return top, link_num


def decoded_rbx(code):
    number = (code >> (8 + ngOffset)) & 0xff

    side = (code >> (16 + ngOffset)) & 0xf
    if side <= 2:
        side = ["", "M", "P"][side]
    else:
        side = "?"

    subdet = (code >> (20 + ngOffset)) & 0xf
    if 1 <= subdet <= 4:
        subdet = ["", "HB", "HE", "HO", "HF"][subdet]
    else:
        subdet = "H?"

    return subdet, side, number


def string56(codes=[], asciifyPatterns=True, regMatchPatterns=True):
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


def string2(code=None):
    slot = (code >> ngOffset) & 0xff
    subdet, side, number = decoded_rbx(code)
    top, link_num = decoded_link(code)
    # return "0x%022x" % code
    return "%s%s%d sl%2d ig%d L%d" % (subdet, side, number, slot, top, link_num)


def string01(code=None):
    top, link_num = decoded_link(code)
    if not top:  # work around bug in 2.x and 3.0
        code = code << 8
        top, link_num = decoded_link(code)
    qie_card = (code >> ngOffset) & 0xf
    rm = (code >> (ngOffset + 4)) & 0xf
    subdet, side, rbx_number = decoded_rbx(code)
    # return "0x%022x" % code
    # return "%s%d%s RM%d card%d link%d" % (subdet, rbx_number, side, rm, qie_card, link_num)
    return "%s%s%d %d %d" % (subdet, side, rbx_number, rm, 2*qie_card + link_num - 1)


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
