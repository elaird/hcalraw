from configuration import hw, matching
import printer


def compare(raw1={}, raw2={}, book=None, anyEmap=False,  printEmap=False,
            printMismatches=False, warnQuality=True, **_):

    if len(raw1) <= 1 or len(raw2) <= 1:
        return

    if anyEmap:
        compare0(raw1, raw2, book, printEmap)
    else:
        compare1(raw1, raw2, book, printMismatches, warnQuality)

    histogram_deltas(raw1, raw2, book)


def nPerChannel(lst=[], iChannel=None):
    return len([x for x in lst if x[-1] == iChannel])


def tsLoop(lst1, lst2, book=None, name=None,
           nBins=None, xMin=None, xMax=None,
           titlea=None, titleb=None, titlec=None):

    assert xMin <= -2  # xMin / 2 used below as a (negative) code

    nPre1, delta1, mp1, cap1 = lst1[:4]
    cap1 = (cap1 + delta1) % 4
    qies1 = lst1[4:]
    n1 = len(qies1)

    if lst2 is None:
        nPre2 = delta2 = mp2 = 0
        cap2 = -2  # dummy
        qies2 = None
        n2 = None
    else:
        nPre2, delta2, mp2, cap2 = lst2[:4]
        cap2 = (cap2 + delta2) % 4
        qies2 = lst2[4:]
        n2 = len(qies2)

    nTsMatched = 0
    nTs = 0

    if "adc" in name and book is not None:
        nCap = 6  # accommodate dummy value above
        book.fill((cap1, cap2), "capid0_vs_capid0",
                  (nCap, nCap), (3.5 - nCap, 3.5 - nCap), (3.5, 3.5),
                  title=titlea)

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


def adc_vs_adc(mapF1, mapF2, book=None, printMismatches=False, iEntry=None, transf=hw.transformed_qie,
               titlePrefix="", name="adc_vs_adc", xMin=-10.5, xMax=127.5):
    matched = []
    misMatched = []

    nBins = int(xMax - xMin)
    titlea = "%s;Samples / bin" % titlePrefix
    titleb = "SOI#semicolon %s" % titlea
    titlec = titleb.replace(";ADC;ADC", ";ADC").replace("semicolon ;", "semicolon;TP;")

    for coords1, lst1 in mapF1.items():
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

        if nTs:
            if nTsMatched == nTs:
                matched.append(coords1)
            else:
                misMatched.append(coords1)
                if printMismatches and coords2 in mapF2:
                    samples1 = tuple(lst1[4:])
                    samples2 = tuple(lst2[4:])
                    q1 = " ".join(["%2x"] * len(samples1)) % samples1
                    q2 = " ".join(["%2x"] * len(samples2)) % samples2
                    c1 = str(coords1)
                    c2 = str(coords2)
                    print("iEntry %d: %s  |  %s  :  %s  |  %s" % (iEntry, c1, c2, q1, q2))
        else:
            # FIXME: handle missing
            pass

    return matched, misMatched


def histogram_nMatched(d, book):
    # histogram n matched
    # nFib = 12 * 12 * 16
    nFib = 14 * 4 * 12 * 8
    bins = (nFib, -0.5, nFib - 0.5)

    nFib2 = 26
    bins2 = (nFib2, -0.5, nFib2 - 0.5)

    for iChannel in range(3):
        title = "Ch%d;number matched;Events / bin" % iChannel
        if d.get("matched") is not None:
            book.fill(nPerChannel(d["matched"], iChannel),
                      "MatchedFibersCh%d" % iChannel,
                      *bins, title=title)

        if d.get("misMatched") is not None:
            book.fill(nPerChannel(d["misMatched"], iChannel),
                      "MisMatchedFibersCh%d" % iChannel,
                      *bins2, title=title.replace("matched", "mis-matched"))

    if d.get("tMatched") is not None:
        book.fill(len(d["tMatched"]), "MatchedTriggerTowers", *bins,
                  title="TPs;number matched;Events / bin")

    if d.get("tMisMatched")is not None:
        book.fill(len(d["tMisMatched"]), "MisMatchedTriggerTowers", *bins2,
                  title="TPs;number mis-matched;Events / bin")


def compare0(raw1, raw2, book, printEmap):
    N1 = raw1[None]
    N2 = raw2[None]
    mapF1, mapB1, _ = dataMap(raw1, book)
    mapF2, mapB2, _ = dataMap(raw2, book)

    N1["matched"], N1["misMatched"] = matchStatsAnyMap(mapF1, mapB2, iStart=4)
    N2["matched"], N2["misMatched"] = matchStatsAnyMap(mapF2, mapB1, iStart=4)
    if printEmap:
        reportMatched(N1["matched"])
        reportFailed(N1["misMatched"])
    histogram_nMatched(N1, book)


def compare1(raw1, raw2, book, printMismatches, warnQuality):
    N1 = raw1[None]
    N2 = raw2[None]
    mapF1, _, _ = dataMap(raw1, book)
    mapF2, _, _ = dataMap(raw2, book)

    if matching.ignoreCE():
        titlePrefix = "!LE"
    else:
        titlePrefix = "!(LE || CE)"
    titlePrefix += ";ADC;ADC"

    N1["matched"], N1["misMatched"] \
        = adc_vs_adc(mapF1, mapF2, book=book, titlePrefix=titlePrefix,
                     printMismatches=printMismatches,
                     iEntry=N1["iEntry"])

    N2["matched"], N2["misMatched"] \
        = adc_vs_adc(mapF2, mapF1, book=None, titlePrefix=titlePrefix)

    tF1 = tpMap(raw1, warnQuality, book)[0]
    tF2 = tpMap(raw2, warnQuality, book)[0]

    N1["tMatched"], N1["tMisMatched"] \
        = adc_vs_adc(tF1, tF2, book=book,
                     name="tp_vs_tp",
                     transf=hw.transformed_tp,
                     xMin=-20.5, xMax=275.5,
                     printMismatches=printMismatches,
                     iEntry=N1["iEntry"])
    # FIXME: N2["tMatched"], N2["tMisMatched"]
    histogram_nMatched(N1, book)


def histogram_deltas(raw1, raw2, book):
    fed1s = [x for x in raw1.keys() if x is not None]
    fed1 = sorted(fed1s)[0]
    d1 = raw1[fed1]
    for fed2, d2 in raw2.items():
        if fed2 is None:
            continue

        utca1 = d1["header"]["utca"]
        utca2 = d2["header"]["utca"]
        bcnDelta = matching.bcnDelta(utca1) - matching.bcnDelta(utca2)

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
    print("%d MATCHED channels:" % len(matched))
    print("uTCA --> VME")
    print("(cr sl   f ch) --> (cr sl   f ch)")
    print("---------------------------------")
    for k in sorted(matched.keys()):
        print("(%s) --> (%s)" % (coordString(*k), coordString(*matched[k])))

    print("\nVME --> uTCA")
    print("(cr sl   f ch) --> (cr sl   f ch)")
    print("---------------------------------")
    lines = []
    for k, v in matched.items():
        lines.append("(%s) --> (%s)" % (coordString(*v), coordString(*k)))
    for l in sorted(lines):
        print(l)
    print("")


def reportFailed(failed=[]):
    print("FAILED fibers %d:" % len(failed))
    if failed:
        print("(fed  h  f ch)")
        print("--------------")
        for c in sorted(failed):
            print("(%s)" % coordString(*c))


def matchStatsAnyMap(fIn={}, bIn={}, iStart=None):
    f = {}
    for coords, dataAll in fIn.items():
        f[coords] = dataAll[iStart:]

    b = {}
    for dataAll, coords in bIn.items():
        b[dataAll[iStart:]] = coords

    matched = {}
    failed = []
    for coords, data in f.items():
        if data in b:
            matched[coords] = b[data]
        else:
            failed.append(coords)
    return matched, failed


def dataMap(raw={}, book=None):
    forward = {}
    backward = {}
    skipped = []

    for fedId, d in raw.items():
        if fedId is None:
            continue

        delta = matching.pipelineDelta(d["header"]["utca"])

        for block in d["htrBlocks"].values():
            nPre = block["nPreSamples"]
            for channelData in block["channelData"].values():
                mp = channelData.get("M&P", 0)
                channel = channelData["FibCh"]
                fiber = channelData["Fiber"]
                coords = (block["Crate"], block["Slot"], block["Top"], fiber, channel)

                if channelData.get("LE") or (channelData.get("CE") and not matching.ignoreCE()):
                    skipped.append(coords)
                    continue

                cap0 = channelData["CapId"][0]
                data = tuple([nPre, delta, mp, cap0] + channelData["QIE"])
                # print coords, data
                forward[coords] = data
                backward[data] = coords
    return forward, backward, skipped


def tpMap(raw={}, warn=True, book=None):
    forward = {}
    backward = {}
    skipped = []

    for fedId, d in raw.items():
        if fedId is None:
            continue

        delta = matching.pipelineDelta(d["header"]["utca"])
        for block in d["htrBlocks"].values():
            for key, triggerData in block["triggerData"].items():
                coords = (block["Crate"], block["Slot"], block["Top"], key)
                nSoi = sum(triggerData["SOI"])
                if warn and nSoi != 1:
                    printer.warning("iEntry %d / %s has !=1 SOIs: %s" % (raw[None]["iEntry"], coords, triggerData["SOI"]))

                if not nSoi:
                    continue

                soi = triggerData["SOI"].index(1)

                l = [soi, delta, 0, 0]
                for i, tp9 in enumerate(triggerData["TP"]):
                    fg = tp9 >> 8
                    tp8 = tp9 & 0xff
                    l.append(tp8)

                    if i == soi:
                        nBins = 14
                        book.fill(tp8, "tp_soi_fg%d_%d" % (fg, fedId), nBins, -0.5, nBins - 0.5, title="FED %d;TP E_{SOI};Trigger Towers / bin" % fedId)
                forward[coords] = l

    return forward, backward, skipped
