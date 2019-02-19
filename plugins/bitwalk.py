def bitwalk(raw1={}, **_):
    keys2 = [x for x in raw1.keys() if x is not None]
    for fedId in sorted(keys2):
        raw = raw1[fedId]

        out = []
        for iBlock, block in sorted(raw["htrBlocks"].items()):
            pd = block.get("patternData")
            if not pd:
                continue

            for fiber1, fd in sorted(block["patternData"].items()):
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
        expected = 1 << int((evn - 1) / 100)  # batches of 100 events
        pattern = (codes[0] & 0xffffffffffffffffffff)  # 80 bits
        if expected ^ pattern:
            print("%3d %2d %2d %2d 0x%020x" % (evn, crate, slot, fiber, pattern))
