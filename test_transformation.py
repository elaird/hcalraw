#!/usr/bin/env python


from configuration.hw import transformed_qie, transformed_tp


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
                c2 = transformed_qie(*c1)
                c3 = transformed_qie(*c2)
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
                c2 = transformed_tp(*c1)
                # c3 = transformed_tp(*c2)
                # if c3 != c1:
                #     print c1, c2, c3
                l.append(c2)

    for slot in [3, 5, 7] + [14, 16, 18]:
        for top, chs in {"t": [0, 1], "b": [4, 5]}.iteritems():
            for ch in chs:
                key = (slb, ch)
                c1 = (crate, slot, top, key)
                c2 = transformed_tp(*c1)
                # c3 = transformed_tp(*c2)
                # if c3 != c1:
                #     print c1, c2, c3
                l.append(c2)
    check(l)


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
