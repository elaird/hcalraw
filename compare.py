from configuration import hw, matching, patterns
import printer
import printRaw
import utils


def flavor(book, d, fedId):
    x = d["Flavor"]
    if x <= 3:
        x = 3
    if 6 <= x:
        x += 1
    if d.get("M&P"):
        x += 1
    book.fill(x, "ChannelFlavor_%d" % fedId, 6, 2.5, 8.5,
              title="FED %d;channel flavor;Channels / bin" % fedId,
              xAxisLabels=["#leq 3", "uTP", "Q 5", "M&P", "Q 6", "7"])


def evnMatchFrac(nMatch, nMisMatch):
    total = nMatch + nMisMatch
    if total:
        return (0.0 + nMatch) / total
    else:
        return -999  # dummy


def labels(crate2bin):
    l = ["-1"] * (1 + len(crate2bin))
    for (cr, top), bin in crate2bin.iteritems():
        assert 1 <= bin
        l[bin - 1] = "%2d%1s" % (cr, top)
    return l


def htrSummary(blocks=[], book=None, fedId=None,
               fedEvn=None, fedOrn5=None, fedBcn=None,
               msg="", warn=True, mismatches=[]):
    nBadHtrs = 0
    caps = {}
    ErrF = {}
    EvN_match = 0
    EvN_misMatch = 0
    adcs = set()
    for i in range(4):
        caps[i] = 0
        ErrF[i] = 0

    crate2bin = {(36, " "): 1,
                 (32, " "): 2,
                 (29, " "): 3,
                 (22, " "): 4,
                 ( 2, "b"): 5,
                 ( 2, "t"): 6,
                 }
    yAxisLabels = labels(crate2bin)
    misMatchMapBins = ((23, 7), (-0.5, 0.5), (22.5, 7.5))

    for block in blocks:
        if type(block) is not dict:
            printer.warning("%s block is not dict" % msg)
            nBadHtrs += 1
            continue
        elif "channelData" not in block:
            printer.warning("%s block has no channelData" % msg)
            nBadHtrs += 1
            continue

        if block["EvN"] == fedEvn:
            EvN_match += 1
        else:
            EvN_misMatch += 1
            if warn:
                printer.warning("%s / slot %2d%1s has EvN 0x%06x" % (msg, block["Slot"], block["Top"], block["EvN"]))

        book.fill(block["EvN"] - fedEvn, "EvN_HTRs_%d" % fedId,
                  11, -5.5, 5.5,
                  title="FED %d;HTR EvN - FED EvN;HTRs / bin" % fedId)

        book.fill(block["OrN5"] - fedOrn5, "OrN5_HTRs_%d" % fedId,
                  11, -5.5, 5.5,
                  title="FED %d;HTR OrN5 - FED OrN5;HTRs / bin" % fedId)

        book.fill(block["BcN"] - fedBcn, "BcN_HTRs_%d" % fedId,
                  11, -5.5, 5.5,
                  title="FED %d;HTR BcN - FED BcN;HTRs / bin" % fedId)

        slot = block["Slot"]
        if slot <= 0:
            slot = 0
        if 22 <= slot:
            slot = 22
        crate = crate2bin.get((block["Crate"], block["Top"]), 7)

        for key, fedVar in [("EvN", fedEvn),
                            ("OrN5", fedOrn5),
                            ("BcN", fedBcn),
                         ]:
            if (block[key] - fedVar):
                book.fill((slot, crate),
                          "%s_mismatch_vs_slot_crate" % key,
                          *misMatchMapBins,
                          title="%s;slot;crate;HTR - FED   mismatches" % key,
                          yAxisLabels=yAxisLabels)

        for otherData in block["otherData"].values():
            flavor(book, otherData, fedId)

        for techData in block["technicalData"].values():
            # remove uHTR pad words from flavor histogram
            if techData["technicalDataType"] or techData["channelId"] or techData["words"]:
                flavor(book, techData, fedId)

        for triggerData in block["triggerData"].values():
            if "Flavor" in triggerData:
                flavor(book, triggerData, fedId)

            book.fill(len(triggerData["TP"]), "nTpSamples_%d" % fedId, 14, -0.5, 13.5,
                      title="FED %d;number of TP samples;Towers / bin" % fedId)

        for channelData in block["channelData"].values():
            flavor(book, channelData, fedId)

            ErrF[channelData["ErrF"]] += 1
            nQie = len(channelData["QIE"])
            book.fill(nQie, "nQieSamples_%d" % fedId, 14, -0.5, 13.5,
                      title="FED %d;number of QIE samples;Channels / bin" % fedId)

            if channelData["ErrF"]:
                book.fill((slot, crate),
                          "ErrFNZ_vs_slot_crate", *misMatchMapBins,
                          title="ErrF != 0;slot;crate;Channels / bin",
                          yAxisLabels=yAxisLabels)
                continue

            book.fill((slot, crate),
                      "ErrF0_vs_slot_crate", *misMatchMapBins,
                      title="ADC mismatch;slot;crate;Channels / bin",
                      yAxisLabels=yAxisLabels)

            coords = (block["Crate"], block["Slot"], block["Top"], channelData["Fiber"], channelData["FibCh"])
            if coords in mismatches:
                book.fill((slot, crate),
                          "ADC_mismatch_vs_slot_crate", *misMatchMapBins,
                          title="ADC mismatch;slot;crate;Channels / bin",
                          yAxisLabels=yAxisLabels)

            caps[channelData["CapId0"]] += 1

            if channelData["QIE"]:
                adc = max(channelData["QIE"])
                adcs.add(adc)
                mp = channelData.get("M&P", 0)
                book.fill(adc, "channel_peak_adc_mp%d_%d" % (mp, fedId), 14, -0.5, 13.5,
                          title="FED %d;Peak ADC (ErrF == 0);Channels / bin" % fedId)

    return nBadHtrs, ErrF, caps, adcs, evnMatchFrac(EvN_match, EvN_misMatch)


def htrOverviewBits(d={}, book={}, fedId=None, msg="", warn=True):
    letters = ["L", "M", "S", "E", "!P", "!V", "!C"]
    abbr = "HTR" if "HTR0" in d else "uHTR"
    for iHtr in range(15):
        key = "%s%d" % (abbr, iHtr)
        if key not in d:
            continue
        h = d[key]

        for i, l in enumerate(letters):
            x = h.get(l[-1])  # .get to handle 'LMS' for VME; last char to avoid '!'
            if x is None:
                continue

            if len(l) == 2:  # flip if !
                x = not x

            if x:
                book.fill(i, "htrOverviewBits_%d" % fedId, 7, -0.5, 6.5,
                          title="FED %d;;HTRs / bin" % fedId,
                          xAxisLabels=letters)
                if warn and d["utca"] and l[-1] == "C":
                    printer.warning("%s / input %2d has bit %s set." % (msg, iHtr, l))


def singleFedPlots(fedId=None, d={}, book={}, warn=True, mismatches=[]):
    book.fill(d["nWord16Skipped"], "nWord16Skipped_%d" % fedId, 14, -0.5, 13.5,
              title="FED %d;nWord16 skipped during unpacking;Events / bin" % fedId)

    h = d["header"]
    t = d["trailer"]
    if "TTS" in t:
        book.fill(t["TTS"], "TTS_%d" % fedId, 16, -0.5, 15.5,
                  title="FED %d;TTS state;Events / bin" % fedId)

    if "BcN" in h:
        book.fill(h["BcN"] / 100.0, "BcN_%d" % fedId, hw.nBx, 0, hw.nBx / 100.0,
                  title="FED %d;BcN / 100;Events / bin" % fedId)

    msg = "FED %d" % fedId
    fedEvn = h.get("EvN")
    fedOrn = h.get("OrN")
    fedBcn = h.get("BcN")

    if fedEvn is None:
        printer.error("FED %d lacks EvN.  Keys: %s" % str(h.keys()))
        msg = ""
    else:
        msg = utils.coords(fedId, fedEvn, fedOrn, fedBcn)

    htrOverviewBits(h, book, fedId, msg=msg, warn=warn)

    nBadHtrs, ErrF, caps, adcs, fracEvN = htrSummary(blocks=d["htrBlocks"].values(),
                                                     book=book,
                                                     fedId=fedId,
                                                     fedEvn=fedEvn,
                                                     fedOrn5=fedOrn & 0x1f,
                                                     fedBcn=fedBcn,
                                                     msg=msg,
                                                     warn=warn,
                                                     mismatches=mismatches)

    errFSum = 0.0 + sum(ErrF.values())

    if errFSum:
        for code, n in ErrF.iteritems():
            title = "FED %d;frac. chan. with ErrF == %d;Events / bin" % (fedId, code)
            book.fill(n/errFSum, "ErrF%d_%d" % (code, fedId), 44, 0.0, 1.1, title=title)

        frac0 = ErrF[0] / errFSum
    else:
        frac0 = -999.  # dummy

    fedTime = utils.minutes(fedOrn, fedBcn)
    book.fillGraph((fedTime, frac0), "frac0_vs_time_%d" % fedId,
                   title=("FED %d" % fedId) +
                   ";time (minutes);frac. chan. with ErrF == 0")

    book.fillGraph((fedTime, fracEvN), "fracEvN_vs_time_%d" % fedId,
                   title=("FED %d" % fedId) +
                   ";time (minutes);frac. HTRs with EvN == FED's")

    book.fillGraph((fedTime, t["nWord64"] * 8.0 / 1024), "kB_vs_time_%d" % fedId,
                   title=("FED %d" % fedId) +
                   ";time (minutes);kB")

    book.fill((fedBcn / 100.0, frac0), "frac0_vs_BcN_%d" % fedId,
              (hw.nBx, 6), (0.0, 0.0), (hw.nBx / 100.0, 1.2),
              title=";FED %d   (BcN / 100);frac. chan. with ErrF == 0;Events / bin" % fedId)

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
        expected = patterns.expectedHtr(fedId, spigot)
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


def loop_over_feds(raw, book, adcTag="", warn=True, mismatches=[]):
    okFeds = set()
    adcs = set()

    for fedId, dct in sorted(raw.iteritems()):
        if fedId is None:
            continue

        book.fill(dct["nBytesSW"] / 1024.0, "nBytesSW_%d" % fedId, 16*8, 0, 16,
                  title="FED %d; kBytes;Events / bin" % fedId)

        fedIdHw = dct["header"]["FEDid"]
        if fedId != fedIdHw:
            printer.error("FED %d has FEDid %d" % (fedId, fedIdHw))
            continue

        nBadHtrs, adcs1 = singleFedPlots(fedId=fedId, d=dct, book=book, warn=warn, mismatches=mismatches)
        adcs = adcs.union(adcs1)
        if nBadHtrs:
            return

        okFeds.add(fedId)
        if (None in raw) and raw[None]["patterns"]:
            if not raw[fedId]["header"]["utca"]:
                checkHtrModules(fedId=fedId, htrBlocks=raw[fedId]["htrBlocks"])

    if adcs:
        book.fill(max(adcs), "max_adc_%s" % adcTag, 128, -0.5, 127.5,
                  title=";max ADC (when ErrF==0);Events / bin")

    return okFeds


def tsLoop(lst1, lst2, book=None, name=None,
           nBins=None, xMin=None, xMax=None,
           titlea=None, titleb=None, titlec=None):

    assert xMin <= -2  # xMin / 2 used below as a (negative) code

    nPre1, delta1, mp1 = lst1[:3]
    qies1 = lst1[3:]
    n1 = len(qies1)

    if lst2 is None:
        nPre2 = delta2 = mp2 = 0
        qies2 = None
        n2 = None
    else:
        nPre2, delta2, mp2 = lst2[:3]
        qies2 = lst2[3:]
        n2 = len(qies2)

    nTsMatched = 0
    nTs = 0

    for i1, qie1 in enumerate(qies1):
        j1 = i1 + delta1
        if j1 < 0 or n1 <= j1:
            continue

        j2 = j1 + delta2 - nPre1 + nPre2
        if n2 is not None and (j2 < 0 or n2 <= j2):
            continue

        if qies2 is None:
            qie2 = xMin / 2  # avoid any match
        else:
            qie2 = qies2[j2]
            nTs += 1

        if qie1 == qie2:
            nTsMatched += 1

        if book is not None:
            book.fill((qie1, qie2), name,
                      (nBins, nBins), (xMin, xMin), (xMax, xMax),
                      title=titlea)
            if i1 == nPre1:
                book.fill((qie1, qie2), "%s_soi_both" % name,
                          (nBins, nBins), (xMin, xMin), (xMax, xMax),
                          title=titleb)

                if 0 <= qie1:
                    book.fill(qie1, "%s_soi1_mp%d" % (name, mp1), nBins, xMin, xMax, title=titlec)
                if 0 <= qie2:
                    book.fill(qie2, "%s_soi2_mp%d" % (name, mp2), nBins, xMin, xMax, title=titlec)

    return nTs, nTsMatched


def adc_vs_adc(mapF1, mapF2, book=None, loud=False, transf=hw.transformed_qie,
               titlePrefix="", name="adc_vs_adc", xMin=-10.5, xMax=127.5):
    matched = []
    misMatched = []

    nBins = int(xMax - xMin)
    titlea = "%s;Samples / bin" % titlePrefix
    titleb = "SOI#semicolon %s" % titlea
    titlec = titleb.replace(";ADC;ADC", ";ADC").replace("semicolon ;", "semicolon;TP;")

    for coords1, lst1 in mapF1.iteritems():
        coords2 = transf(*coords1)
        if coords2 is None:
            continue

        lst2 = mapF2.get(coords2)
        nTs, nTsMatched = tsLoop(lst1, lst2, book,
                                 name, nBins, xMin, xMax,
                                 titlea, titleb, titlec)

        if mapF2 and book is not None:
            if name.startswith("adc"):
                book.fill(nTs, "nTS_for_matching_ADC", 14, -0.5, 13.5,
                          title="ADC;number of TS used for matching;Channels / bin")
            else:
                book.fill(nTs, "nTS_for_matching_TP", 14, -0.5, 13.5,
                          title="TP;number of TS used for matching;Channels / bin")

        if nTsMatched == nTs:
            matched.append(coords1)
        else:
            misMatched.append(coords1)
            if loud and coords2 in mapF2:
                samples1 = tuple(lst1[3:])
                samples2 = tuple(lst2[3:])
                q1 = " ".join(["%2x"] * len(samples1)) % samples1
                q2 = " ".join(["%2x"] * len(samples2)) % samples2
                c1 = str(coords1)
                c2 = str(coords2)
                print "%s  |  %s  :  %s  |  %s" % (c1, c2, q1, q2)

    return matched, misMatched


def histogram_nMatched(book, matched=None, misMatched=None, nonMatched=None, tMatched=None, tMisMatched=None):
    # histogram n matched
    nFib = 228  # = 2 2 3 19;  gt 14 HTRs * 16 fib / HTR
    bins = (nFib, -0.5, nFib - 0.5)

    nFib2 = 18
    bins2 = (nFib2, -0.5, nFib2 - 0.5)

    for iChannel in range(3):
        title = "Ch%d;number matched;Events / bin" % iChannel
        if matched is not None:
            book.fill(nPerChannel(matched, iChannel),
                      "MatchedFibersCh%d" % iChannel,
                      *bins, title=title)

        if misMatched is not None:
            book.fill(nPerChannel(misMatched, iChannel),
                      "MisMatchedFibersCh%d" % iChannel,
                      *bins2, title=title.replace("matched", "mis-matched"))

        if nonMatched is not None:
            book.fill(nPerChannel(nonMatched, iChannel),
                      "NonMatchedFibersCh%d" % iChannel,
                      *bins2, title=title.replace("matched", "non-matched"))

    if tMatched is not None:
        book.fill(len(tMatched), "MatchedTriggerTowers", *bins,
                  title="TPs;number matched;Events / bin")

    if tMisMatched is not None:
        book.fill(len(tMisMatched), "MisMatchedTriggerTowers", *bins,
                  title="TPs;number mis-matched;Events / bin")


def compare(raw1={}, raw2={}, book={}, anyEmap=False,  printEmap=False, warnQuality=True):
    doDump = (1 <= raw1[None]["dump"]) or raw1[None]["patterns"]

    if anyEmap:
        mapF1, mapB1, _ = dataMap(raw1, book)
        mapF2, mapB2, _ = dataMap(raw2, book)
        matched12, nonMatched12 = matchStats(mapF1, mapB2)
        matched21, nonMatched21 = matchStats(mapF2, mapB1)
        misMatched12 = []  # passed to loop_over_feds
        if printEmap:
           reportMatched(matched12)
           reportFailed(nonMatched12)
        histogram_nMatched(book, matched=matched12.keys(), nonMatched=nonMatched12)
    else:
        mapF1, _, _ = dataMap(raw1, book)
        mapF2, _, _ = dataMap(raw2, book)
        titlePrefix = "ErrF == %s;ADC;ADC" % ",".join(["%d" % x for x in matching.okErrF()])
        matched12, misMatched12 = adc_vs_adc(mapF1, mapF2, book=book, titlePrefix=titlePrefix)
        if doDump:
            matched21, misMatched21 = adc_vs_adc(mapF2, mapF1, titlePrefix=titlePrefix)

        tF1 = tpMap(raw1, warnQuality)[0]
        tF2 = tpMap(raw2, warnQuality)[0]

        tMatched12, tMisMatched12 = adc_vs_adc(tF1, tF2, book=book,
                                               name="tp_vs_tp",
                                               transf=hw.transformed_tp,
                                               xMin=-20.5, xMax=255.5)
        tMatched21 = tMisMatched21 = []  # tp_vs_tp(tF2, tF1, book)  # FIXME

        histogram_nMatched(book,
                           matched=matched12, misMatched=misMatched12,
                           tMatched=tMatched12,
                           tMisMatched=tMisMatched12)


    if doDump:
        slim1 = (raw1[None]["dump"] == 1) and (len(raw1) == 2) and not raw2
        printRaw.oneEvent(raw1, nonMatchedQie=misMatched12, nonMatchedTp=tMisMatched12, slim1=slim1)
        printRaw.oneEvent(raw2, nonMatchedQie=misMatched21, nonMatchedTp=tMisMatched21)

    okFeds = loop_over_feds(raw1, book, adcTag="feds1", warn=warnQuality, mismatches=misMatched12)

    noGood = [[], [None]]
    if raw1.keys() in noGood or raw2.keys() in noGood:
        return

    okFeds = okFeds.union(loop_over_feds(raw2, book, adcTag="feds2", warn=warnQuality))

    # histogram some deltas
    fed1 = filter(lambda x: x is not None, sorted(raw1.keys()))[0]
    d1 = raw1[fed1]
    for fed2, d2 in raw2.iteritems():
        if fed2 is None:
            continue

        utca1 = d1["header"]["utca"]
        utca2 = d2["header"]["utca"]
        bcnDelta = matching.bcnDelta(utca1) - matching.bcnDelta(utca2)

        if (fed1 in okFeds) and (fed2 in okFeds):
            for x in ["BcN", "OrN", "EvN"]:
                title = ";".join([x+("%d" % bcnDelta if (x == "BcN" and bcnDelta) else ""),
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


def dataMap(raw={}, book=None):
    forward = {}
    backward = {}
    skipped = []

    for fedId, d in raw.iteritems():
        if fedId is None:
            continue

        delta = matching.pipelineDelta(d["header"]["utca"])

        fiberMap = hw.fiberMap(fedId)
        for block in d["htrBlocks"].values():
            nPre = block["nPreSamples"]
            for channelData in block["channelData"].values():
                mp = channelData.get("M&P", 0)
                channel = channelData["FibCh"]
                fiber = channelData["Fiber"]
                fiber = fiberMap.get(fiber, fiber)
                coords = (block["Crate"], block["Slot"], block["Top"], fiber, channel)

                if channelData["ErrF"] not in matching.okErrF():
                    skipped.append(coords)
                    continue

                data = tuple([nPre, delta, mp] + channelData["QIE"])
                # print coords, data
                forward[coords] = data
                backward[data] = coords
    return forward, backward, skipped


def tpMap(raw={}, warn=True):
    forward = {}
    backward = {}
    skipped = []

    for fedId, d in raw.iteritems():
        if fedId is None:
            continue

        delta = matching.pipelineDelta(d["header"]["utca"])
        for block in d["htrBlocks"].values():
            for key, triggerData in block["triggerData"].iteritems():
                coords = (block["Crate"], block["Slot"], block["Top"], key)
                if warn and sum(triggerData["SOI"]) != 1:
                    printer.warning("%s has !=1 SOIs: %s" % (coords, triggerData["SOI"]))

                i = None
                for i, yes in enumerate(triggerData["SOI"]):
                    if yes:
                        break

                if i is None:
                    continue

                l = [i, delta, 0]
                for tp9 in triggerData["TP"]:
                    l.append(tp9 & 0xff)  # ignore fine-grain bit
                forward[coords] = l

    return forward, backward, skipped
