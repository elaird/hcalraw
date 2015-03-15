#!/usr/bin/env python


from configuration import transformed


def check(l):
    s = set(l)
    if len(l) != len(s):
        print len(l) - len(s)


def one(crate=None, fibCh=None, slots=[], tops="", fibers=[]):
    l = []
    for slot in slots:
        for top in tops:
            for fiber in fibers:
                c1 = (crate, slot, top, fiber, fibCh)
                c2 = transformed(*c1)
                c3 = transformed(*c2)
                if c3 != c1:
                    print c1, c2, c3
                l.append(c2)
    check(l)


if __name__ == "__main__":
    # VME
    one(crate=0,
        fibCh=1,
        slots=range(2, 8) + range(13, 19),
        tops="tb",
        fibers=range(1, 9),
    )

    # uTCA
    one(crate=20,
        fibCh=1,
        slots=range(1, 13),
        tops=" ",
        fibers=range(2, 10) + range(14, 22),
    )
