#!/usr/bin/env python2


from configuration import hw, sw
import utils


def check(l):
    s = set(l)
    if len(l) != len(s):
        print "ERROR: %d collisions." % (len(l) - len(s))
        for item in sorted(l):
            print item


def qie(crate=None, fibCh=None, slots=[], tops="", fibers=[]):
    l = []
    for slot in slots:
        for top in tops:
            for fiber in fibers:
                c1 = (crate, slot, top, fiber, fibCh)
                c2 = hw.transformed_qie(*c1)
                c3 = hw.transformed_qie(*c2)
                if c3 != c1:
                    print c1, c2, c3
                l.append(c2)
    check(l)


def tp_vme_hf(crate=2, slb=6):
    l = []

    for slot in [2, 4, 6] + [13, 15, 17]:
        for top, chs in {"t": [2, 3], "b": [6, 7]}.iteritems():
            for ch in chs:
                key = (slb, ch)
                c1 = (crate, slot, top, key)
                c2 = hw.transformed_tp(*c1)
                # c3 = hw.transformed_tp(*c2)
                # if c3 != c1:
                #     print c1, c2, c3
                l.append(c2)

    for slot in [3, 5, 7] + [14, 16, 18]:
        for top, chs in {"t": [0, 1], "b": [4, 5]}.iteritems():
            for ch in chs:
                key = (slb, ch)
                c1 = (crate, slot, top, key)
                c2 = hw.transformed_tp(*c1)
                # c3 = hw.transformed_tp(*c2)
                # if c3 != c1:
                #     print c1, c2, c3
                l.append(c2)
    check(l)


def shortlists():
    for i, (inp, out), in enumerate([(sw.fedList("HO"), "724-731"),
                                     (sw.fedList("1118,HO"), "724-731,1118"),
                                     (sw.fedList("HCAL"), "724-731,1100,1102,1104,1106,1108,1110,1112,1114,1116,1118-1123,1134"),
                                     (sw.fedList("1118,HO,1111,1118,670"), "670,724-731,1111,1118"),
                                     (sw.fedList("1118,HO,1111,670,671"), "670-671,724-731,1111,1118"),
                                     ([1118, 1134, 1135], "1118,1134-1135"),
                                    ]):
        result = utils.shortList(inp)
        if result != out:
            print "%2d" % i
            print "   Input:", inp
            print "   Expected: ", out
            print "   Result: ", result
            print

    return


if __name__ == "__main__":
    # VME
    qie(crate=0,
        fibCh=1,
        slots=range(2, 8) + range(13, 19),
        tops="tb",
        fibers=range(1, 9),
    )

    # uTCA
    qie(crate=20,
        fibCh=1,
        slots=range(1, 13),
        tops=" ",
        fibers=range(2, 10) + range(14, 22),
    )

    tp_vme_hf()

    shortlists()
