import configuration
import printer
import printRaw


def htrSummary(blocks=[], book=None, fedId=None, msg="", adcPlots=False):
    nBadHtrs = 0
    caps = {}
    ErrF = {}
    for i in range(4):
        caps[i] = 0
        ErrF[i] = 0

    for block in blocks:
        if type(block) is not dict:
            printer.warning("%s block is not dict" % msg)
            nBadHtrs += 1
            continue
        elif "channelData" not in block:
            printer.warning("%s block has no channelData" % msg)
            nBadHtrs += 1
            continue

        book.fill(block["BcN"], "BcN_HTRs_%d" % fedId, 36, 0, 3564,
                  title="FED %d; BcN;HTRs / bin" % fedId)

        for channelData in block["channelData"].values():
            ErrF[channelData["ErrF"]] += 1
            nQie = len(channelData["QIE"].values())
            book.fill(nQie, "nQieSamples_%d" % fedId, 14, -0.5, 13.5,
                      title="FED %d;number of QIE samples;Channels / bin" % fedId)
            if not channelData["ErrF"]:
                caps[channelData["CapId0"]] += 1
                if adcPlots:
                    for adc in channelData["QIE"].values():
                        book.fill(adc, "all_adc", 128, -0.5, 127.5,
                                  title=";all ADC (when ErrF==0); TS / bin")

    return nBadHtrs, ErrF, caps


def singleFedPlots(fedId=None, d={}, book={}, adcPlots=False):
    book.fill(d["nWord16Skipped"], "nWord16Skipped_%d" % fedId, 16, -0.5, 15.5,
              title="FED %d; nWord16 skipped during unpacking;Events / bin" % fedId)

    t = d["trailer"]
    if "TTS" in t:
        book.fill(t["TTS"], "TTS_%d" % fedId, 16, -0.5, 15.5,
                  title="FED %d; TTS state;Events / bin" % fedId)

    msg = "FED %d" % fedId
    if "EvN" in d["header"]:
        msg += " event %d" % d["header"]["EvN"]
    else:
        msg2 = " header lacks EvN.  Keys: %s" % str(d["header"].keys())
        printer.error(msg + msg2)

    nBadHtrs, ErrF, caps = htrSummary(blocks=d["htrBlocks"].values(),
                                      book=book,
                                      fedId=fedId,
                                      msg=msg,
                                      adcPlots=adcPlots)

    errFSum = 0.0 + sum(ErrF.values())
    if errFSum:
        for code, n in ErrF.iteritems():
            book.fill(n/errFSum, "ErrF%d_%d" % (code, fedId), 44, 0.0, 1.1,
                      title="FED %d;frac. chan. w/ErrF==%d;Events / bin" % (fedId, code))

    capSum = 0.0+sum(caps.values())
    if capSum:
        book.fill(max(caps.values())/capSum, "PopCapFrac_%d" % fedId,
                  44, 0.0, 1.1,
                  title=("FED %d" % fedId) +
                  ";frac. ErrF=0 chans w/most pop. capId;Events / bin"
                  )

    book.fill(nBadHtrs, "nBadHtrs_%d" % fedId, 16, -0.5, 15.5,
              title="FED %d; N bad HTRs;Events / bin" % fedId)
    return nBadHtrs


def checkHtrModules(fedId=None, htrBlocks={}):
    crates = []
    for spigot, block in htrBlocks.iteritems():
        if block["IsTTP"]:
            continue
        expected = configuration.expectedHtr(fedId, spigot)
        crates.append(block["Crate"])
        bad = [block["Top"] != expected["Top"],
               block["Slot"] != expected["Slot"],
               ]
        if any(bad):
            fields = (fedId, spigot, block["Crate"],
                      block["Slot"], block["Top"],
                      expected["Slot"], expected["Top"])
            printer.error("FED %3d spigot %2d has moduleId decode to crate %2d slot %2d%s (expected slot %2d%s)" % fields)
    if len(set(crates)) != 1:
        printer.error("FED %s contains modules with crate labels %s." % (str(fedId), str(crates)))


def nPerChannel(lst=[], iChannel=None):
    return len(filter(lambda x: x[-1] == iChannel, lst))


def loop_over_feds(raw, book, adcPlots):
    okFeds = set()
    maxAdc = -1
    for fedId, dct in sorted(raw.iteritems()):
        if fedId is None:
            continue

        book.fill(dct["nBytesSW"]/1024.0, "nBytesSW_%d" % fedId, 64, 0, 16,
                  title="FED %d; kBytes;Events / bin" % fedId)

        fedIdHw = dct["header"]["FEDid"]
        if fedId != fedIdHw:
            printer.error("FED %d has FEDid %d" % (fedId, fedIdHw))
            continue

        if singleFedPlots(fedId=fedId,
                          d=dct,
                          book=book,
                          adcPlots=adcPlots):
            return

        okFeds.add(fedId)
        if (None in raw) and raw[None]["patternMode"]["active"]:
            if not raw[fedId]["header"]["utca"]:
                checkHtrModules(fedId=fedId, htrBlocks=raw[fedId]["htrBlocks"])

        if adcPlots:
            for block in dct["htrBlocks"].values():
                for channelData in block["channelData"].values():
                    if not channelData["ErrF"]:
                        for adc in channelData["QIE"].values():
                            if maxAdc < adc:
                                maxAdc = adc

    if adcPlots and raw is raw1:
        book.fill(maxAdc, "max_adc", 128, -0.5, 127.5,
                  title=";max ADC (when ErrF==0);Events / bin")

    return okFeds


def fill_adc_vs_adc(mapF1, mapF2, book):
    for coords1, samples1  in mapF1.iteritems():
        crate1, slot1, top1, fiber1, fibCh = coords1
        if 2 <= slot1 <= 7:
            slot2 = slot1 - 1
        elif 13 <= slot1 <= 18:
            slot2 = slot1 - 6
        else:
            continue

        crate2 = crate1 + 20
        fiber2 = fiber1 + 1
        if top1 == "t":
            fiber2 += 12

        coords2 = (crate2, slot2, " ", fiber2, fibCh)

        if coords2 in mapF2:
            samples2 = mapF2[coords2]
        else:
            # fmt = "%2d %2d%1s %1d %1d"
            # print (fmt % coords1) + ": " + fmt % coords2
            samples2 = [-1] * len(samples1)
        for i, s1 in enumerate(samples1):
            s2 = samples2[i]
            book.fill((s1, s2),
                      "adc_vs_adc_cr%02d_sl%02d_rx%1d" % (crate2, slot2, 12 <= fiber2),
                      (129, 129),
                      (-1.5, -1.5),
                      (127.5, 127.5),
                      title=";ADC (VME);ADC (uTCA);samples / bin")


def compare(raw1={}, raw2={}, book={}, adcPlots=False, skipErrF=[], skipAllZero=False, adcVsAdc=False):
    okFeds = set()
    for raw in [raw1, raw2]:
        okFeds = okFeds.union(loop_over_feds(raw, book, adcPlots))

    mapF1, mapB1 = dataMap(raw1, skipErrF=skipErrF, skipAllZero=skipAllZero)
    mapF2, mapB2 = dataMap(raw2, skipErrF=skipErrF, skipAllZero=skipAllZero)
    matched12, nonMatched12 = matchStats(mapF1, mapB2)
    matched21, nonMatched21 = matchStats(mapF2, mapB1)

    printRaw.oneEvent(raw1, nonMatched=nonMatched12 if raw2 else [])
    printRaw.oneEvent(raw2, nonMatched=nonMatched21)

    #if nonMatched12:
    #    reportMatched(matched12)
    #    reportFailed(nonMatched12)

    for iChannel in range(3):
        title = ";no. matched fibers (ch%d);Events / bin" % iChannel
        nBins = 400
        bins = (nBins, -0.5, nBins - 0.5)
        book.fill(nPerChannel(matched12.keys(), iChannel),
                  "MatchedFibersCh%d" % iChannel,
                  *bins, title=title)
        book.fill(nPerChannel(nonMatched12, iChannel),
                  "NonMatchedFibersCh%d" % iChannel,
                  *bins, title=title.replace("matched", "non-matched"))

    #some delta plots
    noGood = [[], [None]]
    if raw1.keys() in noGood or raw2.keys() in noGood:
        return
    fed1 = filter(lambda x: x is not None, sorted(raw1.keys()))[0]
    fed2 = filter(lambda x: x is not None, sorted(raw2.keys()))[0]

    utca1 = raw1[fed1]["header"]["utca"]
    utca2 = raw2[fed2]["header"]["utca"]
    bcnDelta = configuration.bcnDelta(utca1) - configuration.bcnDelta(utca2)

    if (fed1 in okFeds) and (fed2 in okFeds):
        for x in ["BcN", "OrN", "EvN"]:
            title = ";".join([x+("%d" % bcnDelta if (x == "BcN") else ""),
                              "FED %s - FED %s" % (fed1, fed2),
                              "Events / bin",
                              ])
            delta = raw1[fed1]["header"][x] - raw2[fed2]["header"][x]
            book.fill(delta, "delta"+x, 11, -5.5, 5.5, title=title)


    if adcVsAdc:
        fill_adc_vs_adc(mapF1, mapF2, book)


def coordString(crate, slot, tb, fiber, channel):
    return "%2d %2d%1s %2d %2d" % (crate, slot, tb, fiber, channel)


def reportMatched(matched={}):
    print "%d MATCHED channels:" % len(matched)
    print "uTCA --> VME"
    print "(cr sl   f ch) --> (cr sl   f ch)"
    print "---------------------------------"
    for k in sorted(matched.keys()):
        print "(%s) --> (%s)" % (coordString(*k), coordString(*matched[k]))

    print
    print "VME --> uTCA"
    print "(cr sl   f ch) --> (cr sl   f ch)"
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


def dataMap(raw={}, skipErrF=[], skipAllZero=None):
    forward = {}
    backward = {}

    for fedId, d in raw.iteritems():
        if fedId is None:
            continue

        utca = d["header"]["utca"]
        fiberMap = configuration.fiberMap(fedId)
        for key, block in d["htrBlocks"].iteritems():
            for channelData in block["channelData"].values():
                channel = channelData["FibCh"]
                matchRange = configuration.matchRange(fedId, block["Slot"], channel, utca)
                fiber = channelData["Fiber"]
                fiber = fiberMap.get(fiber, fiber)
                if channelData["ErrF"] in skipErrF:
                    continue
                coords = (block["Crate"], block["Slot"], block["Top"], fiber, channel)
                qie = channelData["QIE"]
                if len(qie) < len(matchRange):
                    #print "skipping bogus channel",coords
                    continue
                data = tuple([qie.get(i) for i in matchRange])
                if skipAllZero and not any(data):
                    continue
                #print coords,matchRange,[hex(d) for d in data]
                forward[coords] = data
                backward[data] = coords
    return forward, backward
