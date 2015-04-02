def nFibers(utca):
    return 24 if utca else 8


def fiberMap(fedId=None):
    if 989 <= fedId <= 990:  # mCTR2d
        return d2c()
    else:
        return {}


def transformed_crate_slot(crate, slot):
    slot2 = None
    if crate < 20:
        # VME --> uTCA
        crate2 = crate + 20

        if 2 <= slot <= 7:
            slot2 = slot - 1
        elif 13 <= slot <= 18:
            slot2 = slot - 6
    else:
        # uTCA --> VME
        crate2 = crate - 20
        if slot <= 6:
            slot2 = 1 + slot
        elif 7 <= slot <= 12:
            slot2 = 6 + slot
    return (crate2, slot2)


def transformed_qie(crate, slot, top, fiber, fibCh):
    crate2, slot2 = transformed_crate_slot(crate, slot)
    if slot2 is None:
        return None

    if crate < 20:
        # VME --> uTCA
        top2 = " "
        fiber2 = fiber + 1
        if top == "t":
            fiber2 += 12
    else:
        # uTCA --> VME
        fiber2 = fiber - 1
        if 12 <= fiber2:
            fiber2 -= 12
            top2 = "t"
        else:
            top2 = "b"

    return (crate2, slot2, top2, fiber2, fibCh)


def transformed_tp(crate, slot, top, key):
    crate2, slot2 = transformed_crate_slot(crate, slot)
    if slot2 is None:
        return None

    if type(key) is tuple and len(key) == 2 and key[0] == 6:  # VME
        top2 = " "
        slb, ch = key
        if top == "b":
            ch -= 2
        if slot in [2, 4, 6, 13, 15, 17]:
            ch -= 2
        key2 = 0xc0 + ch
    else:
        return None

    return (crate2, slot2, top2, key2)


def d2c():
    return {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
            7:   9,
            8:  11,
            9:  12,
            10: 10,
            11:  8,
            12:  7,
            }
