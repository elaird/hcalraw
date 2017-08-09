def bitwalk(raw1={}, **_):
    for fedId, raw in sorted(raw1.iteritems()):
        if fedId is None:
            continue

        out = []
        for iBlock, block in sorted(raw["htrBlocks"].iteritems()):
            pd = block.get("patternData")
            if not pd:
                continue

            for fiber1, fd in sorted(block["patternData"].iteritems()):
                if 4 <= fd["flavor"]:
                    continue
                check(block["EvN"], block["Crate"], block["Slot"],     fiber1, fd["patternData"], "A")
                check(block["EvN"], block["Crate"], block["Slot"], 1 + fiber1, fd["patternData"], "C")


def check(evn, crate, slot, fiber, patterns, key):
    codes = []
    for p in patterns:
        code = p.get(key + "0")
        if code is None:
            continue
        else:
            codes.append(code)

    if codes:
        expected = 1 << ((evn - 1) / 100)  # batches of 100 events
        pattern = (codes[0] & 0xffffffffffffffffffff)  # 80 bits
        if expected ^ pattern:
            print "%3d %2d %2d %2d 0x%020x" % (evn, crate, slot, fiber, pattern)
