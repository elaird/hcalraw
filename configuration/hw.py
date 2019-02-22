nBx = 3564
f_lhc = 40.079e6  # Hz


def minutes(orn, bcn):
    orn += float(bcn) / nBx
    orbPerSec = f_lhc / nBx
    return orn / orbPerSec / 60.0


def nFibers(utca):
    return 24 if utca else 8


def expectedVmeHtr(fedId, spigot):
    slot = spigot // 2 + (13 if (fedId % 2) else 2)
    if slot == 19:  # DCC occupies slots 19-20
        slot = 21
    return {"Top": {1: "t", 0: "b"}[1 - (spigot % 2)],
            "Slot": slot}


def transformed_crate_slot(crate, slot):
    slot2 = None
    if crate < 20:
        # VME --> uTCA
        crate2 = crate + 20
        if 2 <= slot <= 7:
            slot2 = slot - 1
        elif 13 <= slot <= 18:
            slot2 = slot - 6
        if crate == 7 and slot == 16:  # HO/2018
            crate2 = 38
            slot2 = 1
    else:
        # uTCA --> VME
        crate2 = crate - 20
        if slot <= 6:
            slot2 = 1 + slot
        elif 7 <= slot <= 12:
            slot2 = 6 + slot
        if crate == 38 and slot == 1:  # HO/2018
            crate2 = 7
            slot2 = 16

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

    if type(key) is not tuple or len(key) != 2:  # !VME
        return None

    top2 = " "
    slb, ch = key

    if crate in [2, 9, 12]:  # HF
        if top == "b":
            ch -= 2
        if slot in [2, 4, 6, 13, 15, 17]:
            ch -= 2
        key2 = 0xc0 + ch
    else:
        key2 = (slb - 1) << 4
        ch2 = ch
        if slb == 4 and slot in [3, 4, 14, 15]:
            ch2 = {0: 4,
                   1: 5,
                   2: 0,
                   3: 1,
                   4: 6,
                   5: 7,
                   6: 2,
                   7: 3,
                   }[ch]
        else:
            if 2 <= ch <= 3:
                ch2 += 2
            if 4 <= ch <= 5:
                ch2 -= 2

        key2 += ch2
    return (crate2, slot2, top2, key2)


def d2c():  # mCTR2d
    return {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
            7:   9,
            8:  11,
            9:  12,
            10: 10,
            11:  8,
            12:  7,
            }
