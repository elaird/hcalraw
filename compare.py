import configuration
import printer
import printRaw


def flavor(book, d, fedId):
    book.fill(d["Flavor"], "ChannelFlavor_%d" % fedId, 8, -0.5, 7.5,
              title="FED %d;channel flavor;Channels / bin" % fedId,
              xAxisLabels=["0", "1", "2", "3", "utp", "cpt", "vrb", "tch"])


def htrSummary(blocks=[], book=None, fedId=None,
               fedEvn=None, fedOrn=None, fedBcn=None,
               msg="", adcPlots=False):
    nBadHtrs = 0
    caps = {}
    ErrF = {}
    adcs = set()
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

        book.fill(block["EvN"] - fedEvn, "EvN_HTRs_%d" % fedId,
                  11, -5.5, 5.5,
                  title="FED %d;HTR EvN - FED EvN;HTRs / bin" % fedId)

        book.fill(block["OrN5"] - (fedOrn & 0x1f), "OrN5_HTRs_%d" % fedId,
                  11, -5.5, 5.5,
                  title="FED %d;HTR OrN5 - FED OrN5;HTRs / bin" % fedId)

        book.fill(block["BcN"] - fedBcn, "BcN_HTRs_%d" % fedId,
                  11, -5.5, 5.5,
                  title="FED %d;HTR BcN - FED BcN;HTRs / bin" % fedId)

        for otherData in block["otherData"].values():
            flavor(book, otherData, fedId)

        for otherData in block["technicalData"].values():
            flavor(book, otherData, fedId)

        for triggerData in block["triggerData"].values():
            if "Flavor" in triggerData:
                flavor(book, triggerData, fedId)

            book.fill(len(triggerData["TP"]), "nTpSamples_%d" % fedId, 14, -0.5, 13.5,
                      title="FED %d;number of TP samples;Towers / bin" % fedId)

        for channelData in block["channelData"].values():
            flavor(book, channelData, fedId)

            ErrF[channelData["ErrF"]] += 1
            nQie = len(channelData["QIE"].values())
            book.fill(nQie, "nQieSamples_%d" % fedId, 14, -0.5, 13.5,
                      title="FED %d;number of QIE samples;Channels / bin" % fedId)

            if channelData["ErrF"]:
                continue

            caps[channelData["CapId0"]] += 1
            if adcPlots:
                for adc in channelData["QIE"].values():
                    adcs.add(adc)
                    book.fill(adc, "all_adc", 128, -0.5, 127.5,
                              title=";all ADC (when ErrF==0); TS / bin")

    return nBadHtrs, ErrF, caps, adcs


def htrOverviewBits(d={}, book={}, fedId=None, letters="LMSEPVC"):
    abbr = "HTR" if "HTR0" in d else "uHTR"
    for iHtr in range(15):
        key = "%s%d" % (abbr, iHtr)
        if key not in d:
            continue
        h = d[key]

        for i, l in enumerate(letters):
            if not h.get(l):
                continue
            book.fill(i, "%s_%d" % (letters, fedId), 7, -0.5, 6.5,
                      title="FED %d;;HTRs / bin" % fedId,
                      xAxisLabels=letters)


def singleFedPlots(fedId=None, d={}, book={}, adcPlots=False):
    book.fill(d["nWord16Skipped"], "nWord16Skipped_%d" % fedId, 16, -0.5, 15.5,
              title="FED %d;nWord16 skipped during unpacking;Events / bin" % fedId)

    h = d["header"]
    t = d["trailer"]
    if "TTS" in t:
        book.fill(t["TTS"], "TTS_%d" % fedId, 16, -0.5, 15.5,
                  title="FED %d;TTS state;Events / bin" % fedId)

    if "BcN" in h:
        book.fill(h["BcN"]/100.0, "BcN_%d" % fedId, 99, 0, 35.64,  # = 0.36 * 99
                  title="FED %d;BcN / 100;Events / bin" % fedId)

    msg = "FED %d" % fedId
    fedEvn = h.get("EvN")
    fedOrn = h.get("OrN")
    fedBcn = h.get("BcN")

    if fedEvn is not None:
        msg += " event %d" % fedEvn
    else:
        msg2 = " header lacks EvN.  Keys: %s" % str(h.keys())
        printer.error(msg + msg2)

    htrOverviewBits(h, book, fedId)

    nBadHtrs, ErrF, caps, adcs = htrSummary(blocks=d["htrBlocks"].values(),
                                            book=book,
                                            fedId=fedId,
                                            fedEvn=fedEvn,
                                            fedOrn=fedOrn,
                                            fedBcn=fedBcn,
                                            msg=msg,
                                            adcPlots=adcPlots)

    errFSum = 0.0 + sum(ErrF.values())
    ErrF[13] = ErrF[1] + ErrF[3]

    if errFSum:
        for code, n in ErrF.iteritems():
            title = "FED %d;frac. chan. with ErrF %s;Events / bin" % (fedId, ("== %d" % code) if code != 13 else "!= 0")
            book.fill(n/errFSum, "ErrF%d_%d" % (code, fedId), 44, 0.0, 1.1, title=title)

    capSum = 0.0+sum(caps.values())
    if capSum:
        book.fill(max(caps.values())/capSum, "PopCapFrac_%d" % fedId,
                  44, 0.0, 1.1,
                  title=("FED %d" % fedId) +
                  ";frac. ErrF=0 chans w/most pop. capId;Events / bin"
                  )

    book.fill(nBadHtrs, "nBadHtrs_%d" % fedId, 16, -0.5, 15.5,
              title="FED %d; N bad HTRs;Events / bin" % fedId)
    return nBadHtrs, adcs


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


def loop_over_feds(raw, book, adcPlots, adcTag=""):
    okFeds = set()
    adcs = set()

    for fedId, dct in sorted(raw.iteritems()):
        if fedId is None:
            continue

        book.fill(dct["nBytesSW"]/1024.0, "nBytesSW_%d" % fedId, 64, 0, 16,
                  title="FED %d; kBytes;Events / bin" % fedId)

        fedIdHw = dct["header"]["FEDid"]
        if fedId != fedIdHw:
            printer.error("FED %d has FEDid %d" % (fedId, fedIdHw))
            continue

        nBadHtrs, adcs1 = singleFedPlots(fedId=fedId, d=dct, book=book, adcPlots=adcPlots)
        adcs = adcs.union(adcs1)
        if nBadHtrs:
            return

        okFeds.add(fedId)
        if (None in raw) and raw[None]["patternMode"]:
            if not raw[fedId]["header"]["utca"]:
                checkHtrModules(fedId=fedId, htrBlocks=raw[fedId]["htrBlocks"])

    if adcs:
        book.fill(max(adcs), "max_adc_%s" % adcTag, 128, -0.5, 127.5,
                  title=";max ADC (when ErrF==0);Events / bin")

    return okFeds


def adc_vs_adc(mapF1, mapF2, book=None):
    matched = []
    nonMatched = []
    for coords1, samples1 in mapF1.iteritems():
        coords2 = configuration.transformed_qie(*coords1)
        if coords2 is None:
            continue

        if coords2 in mapF2:
            samples2 = mapF2[coords2]
        else:
            # fmt = "%2d %2d%1s %1d %1d"
            # print (fmt % coords1) + ": " + fmt % coords2
            samples2 = [-1] * len(samples1)

        if samples1 == samples2:
            matched.append(coords1)
        else:
            nonMatched.append(coords1)

        if book is not None:
            crate2, slot2, top2, fiber2, _ = coords2

            if top2 == " ":
                rx = 12 <= fiber2
            else:
                rx = "bt".find(top2)

            xMin = -10.5
            xMax = 127.5
            nBins = int(xMax - xMin)
            for i, s1 in enumerate(samples1):
                s2 = samples2[i]
                book.fill((s1, s2), "adc_vs_adc",
                          #"adc_vs_adc_cr%02d_sl%02d_rx%1d" % (crate2, slot2, rx),
                          (nBins, nBins), (xMin, xMin), (xMax, xMax),
                          title=";ADC;ADC;samples / bin")
    return matched, nonMatched


def tp_vs_tp(mapF1, mapF2, book=None):
    matched = []
    nonMatched = []

    for coords1, samples1 in mapF1.iteritems():
        coords2 = configuration.transformed_tp(*coords1)
        if coords2 is None:
            continue

        if coords2 in mapF2:
            samples2 = mapF2[coords2]
        else:
            samples2 = [-1] * len(samples1)

        if samples1 == samples2:
            matched.append(coords1)
        else:
            nonMatched.append(coords1)

        if book:
            xMin = -25.5
            xMax = 255.5
            nBins = int(xMax - xMin)
            for i, s1 in enumerate(samples1):
                s2 = samples2[i]
                book.fill((s1, s2), "tp_vs_tp",
                          (nBins, nBins), (xMin, xMin), (xMax, xMax),
                          title=";TP;TP;samples / bin")
    return matched, nonMatched


def compare(raw1={}, raw2={}, book={}, anyEmap=False,  printEmap=False, adcPlots=False):
    dump = (1 <= raw1[None]["dump"]) or raw1[None]["patternMode"]

    if anyEmap:
        mapF1, mapB1, _ = dataMap(raw1)
        mapF2, mapB2, _ = dataMap(raw2)
        matched12, nonMatched12 = matchStats(mapF1, mapB2)
        matched21, nonMatched21 = matchStats(mapF2, mapB1)
        tMatched12 = tNonMatched12 = []
        tMatched21 = tNonMatched21 = []

        if printEmap:
           reportMatched(matched12)
           reportFailed(nonMatched12)
    else:
        mapF1 = dataMap(raw1)[0]
        mapF2 = dataMap(raw2)[0]
        matched12, nonMatched12 = adc_vs_adc(mapF1, mapF2, book)
        if dump:
            matched21, nonMatched21 = adc_vs_adc(mapF2, mapF1)

        tF1 = tpMap(raw1)[0]
        tF2 = tpMap(raw2)[0]
        tMatched12, tNonMatched12 = tp_vs_tp(tF1, tF2, book)
        tMatched21 = tNonMatched21 = []  # tp_vs_tp(tF2, tF1, book)  # FIXME

    if dump:
        printRaw.oneEvent(raw1, nonMatchedQie=nonMatched12, nonMatchedTp=tNonMatched12)
        printRaw.oneEvent(raw2, nonMatchedQie=nonMatched21, nonMatchedTp=tNonMatched21)

    okFeds = loop_over_feds(raw1, book, adcPlots, adcTag="feds1")

    noGood = [[], [None]]
    if raw1.keys() in noGood or raw2.keys() in noGood:
        return

    okFeds = okFeds.union(loop_over_feds(raw2, book, adcPlots, adcTag="feds2"))

    # histogram n matched
    nFib = 228  # = 2 2 3 19;  gt 14 HTRs * 16 fib / HTR
    bins = (nFib, -0.5, nFib - 0.5)
    for iChannel in range(3):
        title = ";no. matched fibers (ch%d);Events / bin" % iChannel
        book.fill(nPerChannel(matched12.keys() if anyEmap else matched12, iChannel),
                  "MatchedFibersCh%d" % iChannel,
                  *bins, title=title)
        book.fill(nPerChannel(nonMatched12, iChannel),
                  "NonMatchedFibersCh%d" % iChannel,
                  *bins, title=title.replace("matched", "non-matched"))

    book.fill(len(tMatched12), "MatchedTriggerTowers", 60, -0.5, 59.5, title=";no. matched TPs;Events / bin")

    # histogram some deltas
    fed1 = filter(lambda x: x is not None, sorted(raw1.keys()))[0]
    d1 = raw1[fed1]
    for fed2, d2 in raw2.iteritems():
        if fed2 is None:
            continue

        utca1 = d1["header"]["utca"]
        utca2 = d2["header"]["utca"]
        bcnDelta = configuration.bcnDelta(utca1) - configuration.bcnDelta(utca2)

        if (fed1 in okFeds) and (fed2 in okFeds):
            for x in ["BcN", "OrN", "EvN"]:
                title = ";".join([x+("%d" % bcnDelta if (x == "BcN") else ""),
                                  "FED %s - FED %s" % (fed1, fed2),
                                  "Events / bin",
                                  ])
                delta = d1["header"][x] - d2["header"][x]
                book.fill(delta, "delta%s_%s_%s" % (x, fed1, fed2), 11, -5.5, 5.5, title=title)


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


def dataMap(raw={}):
    skipErrF = configuration.matchSkipErrF

    forward = {}
    backward = {}
    skipped = []

    for fedId, d in raw.iteritems():
        if fedId is None:
            continue

        utca = d["header"]["utca"]
        fiberMap = configuration.fiberMap(fedId)
        for block in d["htrBlocks"].values():
            for channelData in block["channelData"].values():
                channel = channelData["FibCh"]
                fiber = channelData["Fiber"]
                fiber = fiberMap.get(fiber, fiber)
                coords = (block["Crate"], block["Slot"], block["Top"], fiber, channel)

                if channelData["ErrF"] in skipErrF:
                    skipped.append(coords)
                    continue

                matchRange = configuration.matchRange(fedId, block["Slot"], channel, utca)
                qie = channelData["QIE"]
                if len(qie) < len(matchRange):
                    skipped.append(coords)
                    continue

                data = tuple([qie.get(i) for i in matchRange])
                # print coords, matchRange, [hex(d) for d in data]
                forward[coords] = data
                backward[data] = coords
    return forward, backward, skipped


def tpMap(raw={}):
    skipErrF = configuration.matchSkipErrF

    forward = {}
    backward = {}
    skipped = []

    for fedId, d in raw.iteritems():
        if fedId is None:
            continue

        utca = d["header"]["utca"]
        for block in d["htrBlocks"].values():
            for key, triggerData in block["triggerData"].iteritems():
                coords = (block["Crate"], block["Slot"], block["Top"], key)
                forward[coords] = [x & 0xff for x in triggerData["TP"]]  # ignore fine-grain bit

    return forward, backward, skipped
