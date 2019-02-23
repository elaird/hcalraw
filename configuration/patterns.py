import re

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


def ng_looks_broken(i):
    return bool((i >> 56) & 0xffff) or not i


def string2(code=None):
    slot = (code >> ngOffset) & 0xff
    subdet, side, number = decoded_rbx(code)
    top, link_num = decoded_link(code)

    if ng_looks_broken(code):
        return "0x%022x" % code
    else:
        return "%s%s%02d %2d %d" % (subdet, side, number, slot, 7 + link_num - 3 * top)


def string013(code=None, flavor=None):
    top, link_num = decoded_link(code)
    qie_card = (code >> ngOffset) & 0xf
    rm = (code >> (ngOffset + 4)) & 0xf
    subdet, side, rbx_number = decoded_rbx(code)
    if ng_looks_broken(code):
        return "0x%022x" % code

    if flavor == 3:  # FIXME
        if rm in [1, 3]:
            rm_fibs = [3, 2, 1, 8, 7, 6, 5, 4]
        elif rm in [2, 4]:
            rm_fibs = [4, 5, 6, 7, 8, 1, 2, 3]
        else:
            rm_fibs = [2, 1]
        rm_fib = rm_fibs[2 * (qie_card - 1) + top]
    else:
        rm_fib = 2 * qie_card - 1 + link_num

    return "%s%s%02d %2d %d" % (subdet, side, rbx_number, rm, rm_fib)


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
            365: 13}.get(fedId // 2, -1)
