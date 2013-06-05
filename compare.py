import printRaw


def singleFedPlots(raw={}, fedId=None, book={}):
    if fedId is None:
        return
    d = raw[fedId]
    book.fill(d["TTS"], "TTS_%d" % fedId, 16, -0.5, 15.5,
              title="FED %d; TTS state;Events / bin" % fedId)

    caps = {0: 0, 1: 0, 2: 0, 3: 0}
    ErrF = {0: 0, 1: 0, 2: 0, 3: 0}
    for block in d["htrBlocks"].values():
        for channelId, channelData in block["channelData"].iteritems():
            ErrF[channelData["ErrF"]] += 1
            if not channelData["ErrF"]:
                caps[channelData["CapId0"]] += 1
    errFSum = 0.0+sum(ErrF.values())
    if errFSum:
        book.fill(ErrF[0]/errFSum, "ErrF0_%d" % fedId, 44, 0.0, 1.1,
                  title="FED %d;frac. chan. w/ErrF==0;Events / bin" % fedId)

    capSum = 0.0+sum(caps.values())
    if capSum:
        book.fill(max(caps.values())/capSum, "PopCapFrac_%d" % fedId,
                  44, 0.0, 1.1,
                  title=("FED %d" % fedId) +
                  ";frac. ErrF=0 chans w/most pop. capId;Events / bin"
                  )


def compare(raw1={}, raw2={}, book={}):
    hyphens = True
    if raw1 and raw1[None]["printFiberChannels"]:
        printRaw.oneEvent(raw1, hyphens)
        hyphens = False
    if raw2 and raw2[None]["printFiberChannels"]:
        printRaw.oneEvent(raw2, hyphens)

    for raw in [raw1, raw2]:
        for fedId, dct in raw.iteritems():
            singleFedPlots(raw, fedId, book)

    mapF1, mapB1 = dataMap(raw1)
    mapF2, mapB2 = dataMap(raw2)
    matched, failed = matchStats(mapF1, mapB2)

    if failed:
        reportMatched(matched)
        reportFailed(failed)

    book.fill(len(matched), "MatchedFibers", 24, -0.5, 23.5, title=";no. matched fibers;events / bin")
    book.fill(len(failed),   "FailedFibers", 24, -0.5, 23.5, title=";no. non-matched fibers;events / bin")

    #some delta plots
    noGood = [[], [None]]
    if raw1.keys() in noGood or raw2.keys() in noGood:
        return
    fed1 = filter(lambda x: x is not None, raw1.keys())[0]
    fed2 = filter(lambda x: x is not None, raw2.keys())[0]

    delta = raw1[None]["bcnDelta"]-raw2[None]["bcnDelta"]
    for x in ["BcN", "OrN", "EvN"]:
        title = ";".join([x+("%d" % delta if (x == "BcN") else ""),
                          "FED %s - FED %s" % (fed1, fed2),
                          "Events / bin",
                              ])
        book.fill(raw1[fed1][x] - raw2[fed2][x], "delta"+x, 11, -5.5, 5.5, title=title)


def coordString(fedId, moduleId, fiber, channel):
    return "%3d %2d %2d %2d" % (fedId, moduleId, fiber, channel)


def reportMatched(matched={}):
    print "MATCHED fibers %d:" % len(matched)
    print "uTCA --> CMS"
    print "(fed  h  f ch) --> (fed  h  f ch)"
    print "---------------------------------"
    for k in sorted(matched.keys()):
        print "(%s) --> (%s)" % (coordString(*k), coordString(*matched[k]))

    print
    print "CMS --> uTCA"
    print "(fed  h  f ch) --> (fed  h  f ch)"
    print "---------------------------------"
    lines = []
    for k, v in matched.iteritems():
        lines.append("(%s) --> (%s)" % (coordString(*v), coordString(*k)))
    for l in sorted(lines):
        print l
    print

def reportFailed(failed=[]):
    print "FAILED fibers %d:" % len(failed)
    if failed:
        print "(fed  h  f ch)"
        print "--------------"
        for c in sorted(failed):
            print "(%s)" % coordString(*c)


def matchStats(f={}, b={}):
    matched = {}
    failed = []
    for coords, data in f.iteritems():
        if data in b:
            matched[coords] = b[data]
        else:
            failed.append(coords)
    return matched, failed


def dataMap(raw={}):
    forward = {}
    backward = {}

    fiberMap = raw[None]["fiberMap"]
    for fedId, d in raw.iteritems():
        if fedId is None:
            continue

        matchRange = raw[None]["matchRange"][fedId]
        for key, block in d["htrBlocks"].iteritems():
            if fedId >= 900: # FIXME: check uTCA
                moduleId = block["ModuleId"] & 0xf
                if fedId == 989 and moduleId >= 5:  # FIXME: hack for HF timing (Jan. slice-test)
                    matchRange = raw[None]["matchRange"][990]
            else:
                moduleId = block["ModuleId"] & 0x1f

            for channelId, channelData in block["channelData"].iteritems():
                channel = channelId % 4
                fiber = 1+channelId/4  # integer division
                fiber = fiberMap[fiber] if fiber in fiberMap else fiber
                if channel != 1:
                    continue
                if channelData["ErrF"] & 0x2:
                    continue
                coords = (fedId, moduleId, fiber, channel)
                qie = channelData["QIE"]
                if len(qie) < len(matchRange):
                    #print "skipping bogus channel",coords
                    continue
                data = tuple([qie[i] for i in matchRange])
                #print coords,matchRange,[hex(d) for d in data]
                forward[coords] = data
                backward[data] = coords
    return forward, backward
