import configuration
import printer
import printRaw


def singleFedPlots(raw={}, fedId=None, book={}):
    d = raw[fedId]
    t = d["trailer"]
    if "TTS" in t:
        book.fill(t["TTS"], "TTS_%d" % fedId, 16, -0.5, 15.5,
                  title="FED %d; TTS state;Events / bin" % fedId)

    caps = {0: 0, 1: 0, 2: 0, 3: 0}
    ErrF = {0: 0, 1: 0, 2: 0, 3: 0}
    for block in d["htrBlocks"].values():
        for channelData in block["channelData"].values():
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


def checkHtrModules(fedId=None, htrBlocks={}):
    crates = []
    for spigot, block in htrBlocks.iteritems():
        expectedTop = 1 - (spigot % 2)
        expectedSlot = spigot/2 + (13 if (fedId % 2) else 2)
        if expectedSlot == 19:  # DCC occupies slots 19-20
            expectedSlot = 21

        id = block["ModuleId"]
        # http://isscvs.cern.ch/cgi-bin/viewcvs-all.cgi/TriDAS/hcal/hcalHW/src/common/hcalHTR.cc?revision=1.88&root=tridas&view=markup
        # int id=(m_crate<<6)+((m_slot&0x1F)<<1)+((true_for_top)?(1):(0));
        # fpga->dev->write("HTRsubmodN",id);
        top = id & 0x1
        slot = (id >> 1) & 0x1f
        crate = (id >> 6)
        crates.append(crate)

        bad = [top != expectedTop,
               slot != expectedSlot,
               ]
        if any(bad):
            fields = (fedId, spigot, crate, slot, "top" if top else "bot", expectedSlot, "top" if expectedTop else "bot")
            printer.error("FED %3d spigot %2d has moduleId decode to crate %2d slot %2d %3s (expected slot %2d %3s)" % fields)
    if len(set(crates)) != 1:
        printer.error("FED %s contains modules with crate labels %s." % (str(fedId), str(crates)))


def nPerChannel(lst=[], iChannel=None):
    return len(filter(lambda x: x[-1] == iChannel, lst))


def compare(raw1={}, raw2={}, book={}):
    printRaw.oneEvent(raw1)
    printRaw.oneEvent(raw2)

    for raw in [raw1, raw2]:
        for fedId, dct in raw.iteritems():
            if fedId is None:
                continue
            singleFedPlots(raw, fedId, book)
            if (None in raw) and raw[None]["patternMode"]:
                checkHtrModules(fedId, raw[fedId]["htrBlocks"])

    mapF1, mapB1 = dataMap(raw1)
    mapF2, mapB2 = dataMap(raw2)
    matched, failed = matchStats(mapF1, mapB2)

    #if failed:
    #    reportMatched(matched)
    #    reportFailed(failed)

    for iChannel in range(3):
        title = ";no. matched fibers (ch%d);events / bin" % iChannel
        nBins = 24
        bins = (nBins, -0.5, nBins - 0.5)
        book.fill(nPerChannel(matched.keys(), iChannel),
                  "MatchedFibersCh%d" % iChannel,
                  *bins, title=title)
        book.fill(nPerChannel(failed, iChannel),
                  "FailedFibersCh%d" % iChannel,
                  *bins, title=title.replace("matched", "non-matched"))

    #some delta plots
    noGood = [[], [None]]
    if raw1.keys() in noGood or raw2.keys() in noGood:
        return
    fed1 = filter(lambda x: x is not None, raw1.keys())[0]
    fed2 = filter(lambda x: x is not None, raw2.keys())[0]

    delta = configuration.bcnDelta(fed1) - configuration.bcnDelta(fed2)
    for x in ["BcN", "OrN", "EvN"]:
        title = ";".join([x+("%d" % delta if (x == "BcN") else ""),
                          "FED %s - FED %s" % (fed1, fed2),
                          "Events / bin",
                          ])
        book.fill(raw1[fed1]["header"][x] - raw2[fed2]["header"][x], "delta"+x, 11, -5.5, 5.5, title=title)


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

    fiberMap = configuration.fiberMap()

    for fedId, d in raw.iteritems():
        if fedId is None:
            continue

        matchRange = configuration.matchRange(fedId)
        for key, block in d["htrBlocks"].iteritems():
            if not configuration.isVme(fedId):
                moduleId = block["ModuleId"] & 0xf
                if fedId == 989 and moduleId >= 5:  # FIXME: hack for HF timing (Jan. slice-test)
                    matchRange = configuration.matchRange(990)
            else:
                moduleId = block["ModuleId"] & 0x1f

            for channelData in block["channelData"].values():
                channel = channelData["FibCh"]
                fiber = 1 + channelData["Fiber"]
                fiber = fiberMap[fiber] if fiber in fiberMap else fiber
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
