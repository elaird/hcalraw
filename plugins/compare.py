from configuration import hw, matching, patterns
from plugins.printraw import spigotList
import printer
import utils


def flavor(book, d, fedId):
    x = d["Flavor"]
    if x == 0:
        x = 1
    if x == 3:
        x = 7
    if 4 <= x:
        x -= 1
    book.fill(x, "ChannelFlavor_%d" % fedId, 7, 0.5, 7.5,
              title="FED %d;channel flavor;Channels / bin" % fedId,
              xAxisLabels=["HE", "HF", "uTP", "Q5", "Q6", "7", "?"])


def matchFrac(nMatch, nMisMatch):
    total = nMatch + nMisMatch
    if total:
        return (0.0 + nMatch) / total
    else:
        return None


def labels(crate2bin):
    l = ["-1"] * (1 + len(crate2bin))
    for (cr, top), bin in crate2bin.iteritems():
        assert 1 <= bin
        l[bin - 1] = "%2d%1s" % (cr, top)
    return l


def slot2bin(slot, min=0, max=22):
    if slot <= min:
        return min
    if max <= slot:
        return max
    return slot


def histogramBlock(book, block, fedId, fedEvn, fedOrn5, fedBcn):
    evnMask = 0x7f
    book.fill((fedEvn & evnMask, block["EvN"] & evnMask), "EvN_HTR_vs_FED_%d" % fedId,
              (evnMask, evnMask), (-0.5, -0.5), (evnMask - 0.5, evnMask - 0.5),
              title="FED %d;FED EvN & 0x%x;HTR EvN & 0x%x;HTRs / bin" % (fedId, evnMask, evnMask))

    ornMask = 0x1f
    book.fill((fedOrn5, block["OrN5"]), "OrN5_HTR_vs_FED_%d" % fedId,
              (ornMask, ornMask), (-0.5, -0.5), (ornMask - 0.5, ornMask - 0.5),
              title="FED %d;FED OrN5;HTR OrN5;HTRs / bin" % fedId)

    book.fill(block["EvN"] - fedEvn, "EvN_HTRs_%d" % fedId,
              11, -5.5, 5.5,
              title="FED %d;HTR EvN - FED EvN;HTRs / bin" % fedId)

    book.fill(block["OrN5"] - fedOrn5, "OrN5_HTRs_%d" % fedId,
              11, -5.5, 5.5,
              title="FED %d;HTR OrN5 - FED OrN5;HTRs / bin" % fedId)

    book.fill(block["BcN"] - fedBcn, "BcN_HTRs_%d" % fedId,
              11, -5.5, 5.5,
              title="FED %d;HTR BcN - FED BcN;HTRs / bin" % fedId)


def histogramBlock2(book, block, fedEvn, fedOrn5, fedBcn, slotCrate, misMatchMapBins, yAxisLabels):
    book.fill(slotCrate,
              "block_vs_slot_crate",
              *misMatchMapBins,
              title="any;slot;crate;HTR / bin",
              yAxisLabels=yAxisLabels)

    for key, fedVar in [("EvN", fedEvn),
                        ("OrN5", fedOrn5),
                        ("BcN", fedBcn),
                         ]:
        if (block[key] - fedVar):
            book.fill(slotCrate,
                      "%s_mismatch_vs_slot_crate" % key,
                      *misMatchMapBins,
                      title="%s mismatch;slot;crate;HTR - FED   mismatches / bin" % key,
                      yAxisLabels=yAxisLabels)


def htrSummary(blocks=[], book=None, fedId=None,
               fedEvn=None, fedOrn5=None, fedBcn=None,
               msg="", warn=True, fewerHistos=False, fedTime=None,
               **other):
    nBadHtrs = 0
    caps = {}
    ErrF = {}

    nEvnMatch = 0
    nEvnMisMatch = 0

    nAdcMatch = 0
    nAdcMisMatch = 0

    nTpMatch = 0
    nTpMisMatch = 0

    adcs = set()
    for i in range(4):
        caps[i] = 0
        ErrF[i] = 0

    crate2bin = {
        #  3 904 uTCA crates
        # 13 USC uTCA crates
        (63, " "):  1, (62, " "):  2,
        (61, " "):  3,
        (37, " "):  4, (36, " "):  5,
        (35, " "):  6, (34, " "):  7,
        (32, " "):  8, (31, " "):  9,
        (30, " "): 10, (29, " "): 11,
        (25, " "): 12, (24, " "): 13,
        (22, " "): 14, (21, " "): 15,
        (20, " "): 16,
        # 9 USC VME HBHE crates
        # (17, "b"): 14, (17, "t"): 15,
        # (15, "b"): 16, (15, "t"): 17,
        # (14, "b"): 18, (14, "t"): 19,
        # (11, "b"): 20, (11, "t"): 21,
        # (10, "b"): 22, (10, "t"): 23,
        # ( 5, "b"): 24, ( 5, "t"): 25,
        # ( 4, "b"): 26, ( 4, "t"): 27,
        # ( 1, "b"): 28, ( 1, "t"): 29,
        # ( 0, "b"): 30, ( 0, "t"): 31,
    }

    crateFail = 1 + max(crate2bin.values())
    yAxisLabels = labels(crate2bin)
    misMatchMapBins = ((13, crateFail), (-0.5, 0.5), (12.5, 0.5 + crateFail))

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
            nEvnMatch += 1
        else:
            nEvnMisMatch += 1
            if warn:
                printer.warning("%s / crate %2d slot %2d%1s has EvN 0x%06x" % (msg, block["Crate"], block["Slot"], block["Top"], block["EvN"]))

        histogramBlock(book, block, fedId, fedEvn, fedOrn5, fedBcn)
        slotCrate = (slot2bin(block["Slot"]), crate2bin.get((block["Crate"], block["Top"]), crateFail))
        histogramBlock2(book, block, fedEvn, fedOrn5, fedBcn, slotCrate, misMatchMapBins, yAxisLabels)

        nTpTowerBins = 50
        book.fill(len(block["triggerData"]), "nTpTowers_%d" % fedId, nTpTowerBins, -0.5, nTpTowerBins - 0.5,
                  title="FED %d;number of TP towers;HTRs / bin" % fedId)

        nChannelBins = 75
        book.fill(len(block["channelData"]), "nChannels_%d" % fedId, nChannelBins, -0.5, 2*nChannelBins - 0.5,
                  title="FED %d;number of channels;HTRs / bin" % fedId)

        if fewerHistos:
            continue

        for otherData in block["otherData"].values():
            flavor(book, otherData, fedId)

        for techData in block["technicalData"].values():
            # remove uHTR pad words from flavor histogram
            if techData["technicalDataType"] or techData["channelId"] or techData["words"]:
                flavor(book, techData, fedId)

        for triggerKey, triggerData in block["triggerData"].iteritems():
            if "Flavor" in triggerData:
                flavor(book, triggerData, fedId)

            tpMatch = histogramTriggerData(book, block, triggerData, triggerKey, fedId,
                                           crate2bin, crateFail, slotCrate, misMatchMapBins, yAxisLabels,
                                           tpMatches=other.get("tMatched", []), # tpMismatches,
                                          )
            if tpMatch:
                nTpMatch += 1
            else:
                nTpMisMatch += 1

        for channelData in block["channelData"].values():
            flavor(book, channelData, fedId)
            a, b = histogramChannelData(book, block, channelData, fedId,
                                        caps, ErrF, adcs, crate2bin, crateFail,
                                        slotCrate, misMatchMapBins,
                                        yAxisLabels, fedTime, **other)
            nAdcMatch += a
            nAdcMisMatch += b

    return [nBadHtrs, ErrF, caps, adcs,
            matchFrac(nEvnMatch, nEvnMisMatch),
            matchFrac(nAdcMatch, nAdcMisMatch),
            matchFrac(nTpMatch, nTpMisMatch),
            ]


def histogramTriggerData(book, block, triggerData, triggerKey, fedId,
                         crate2bin, crateFail, slotCrate, misMatchMapBins, yAxisLabels,
                         tpMatches=None, # tpMismatches,
                         ):

    book.fill(len(triggerData["TP"]), "nTpSamples_%d" % fedId, 14, -0.5, 13.5,
              title="FED %d;number of TP samples;Towers / bin" % fedId)

    maxTp = -1
    for tp in triggerData["TP"]:
        tp8 = tp & 0xff  # ignore fine-grain bit
        if maxTp < tp8:
            maxTp = tp8
    if 0 <= maxTp:
        book.fill(maxTp, "channel_peak_tp_%d" % fedId, 14, -0.5, 13.5,
                  title="FED %d;Peak TP E;Towers / bin" % fedId)

    tpCoords = (block["Crate"], block["Slot"], block["Top"], triggerKey)
    tpCoords2 = hw.transformed_tp(*tpCoords)
    if tpCoords2 is None:
        book.fill(slotCrate, "TP_unmatchable_vs_slot_crate", *misMatchMapBins,
                  title="TP unmatchable;slot;crate;Towers / bin",
                  yAxisLabels=yAxisLabels)
        return

    crate2, slot2, top2 = tpCoords2[:3]
    slotsCrates = [slotCrate,
                   (slot2bin(slot2), crate2bin.get((crate2, top2), crateFail)),
                   ]

    for t in slotsCrates:
        book.fill(t, "TP_matchable_vs_slot_crate", *misMatchMapBins,
                  title="TP matchable;slot;crate;Towers / bin",
                  yAxisLabels=yAxisLabels)

    if tpCoords in tpMatches:
        return True
    else:
        for t in slotsCrates:
            book.fill(t, "TP_mismatch_vs_slot_crate", *misMatchMapBins,
                      title="TP mismatch;slot;crate;Towers / bin",
                      yAxisLabels=yAxisLabels)
        return False


def histogramChannelData(book, block, channelData, fedId,
                         caps, ErrF, adcs, crate2bin, crateFail,
                         slotCrate, misMatchMapBins,
                         yAxisLabels, fedTime, **other):

    nAdcMatch = 0
    nAdcMisMatch = 0

    ErrF[channelData["ErrF"]] += 1
    book.fill(len(channelData["QIE"]), "nQieSamples_%d" % fedId, 14, -0.5, 13.5,
              title="FED %d;number of QIE samples;Channels / bin" % fedId)

    book.fill(slotCrate,
              "ErrFAny_vs_slot_crate", *misMatchMapBins,
              title="any;slot;crate;Channels / bin",
              yAxisLabels=yAxisLabels)

    # if block["Slot"] == 9 and block["Crate"] == 41 and channelData["Fiber"] == 2 and channelData["FibCh"] == 3:
    #     for i in [0, 1]:
    #         title = "cr41_sl9_fib2_fibch3_ts%d" % i
    #         book.fill(channelData["QIE"][i], title, 256, -0.5, 255.5,
    #                   title="%s;ADC;Counts / bin" % title)

    if channelData["ErrF"]:
        for name, title in [("ErrFNZ", "ErrF != 0"),
                            ("ErrF%d" % channelData["ErrF"], "ErrF == %d" % channelData["ErrF"]),
                            ]:
            book.fill(slotCrate,
                      "%s_vs_slot_crate" % name, *misMatchMapBins,
                      title="%s;slot;crate;Channels / bin" % title,
                      yAxisLabels=yAxisLabels)
        return nAdcMatch, nAdcMisMatch

    book.fill(slotCrate,
              "ErrF0_vs_slot_crate", *misMatchMapBins,
              title="ErrF == 0;slot;crate;Channels / bin",
              yAxisLabels=yAxisLabels)

    book.fill((block["Slot"], channelData["Fiber"]),
              "fiber_vs_slot_%d" % fedId, (12, 24), (0.5, -0.5), (12.5, 23.5),
              title="FED %d;Slot;Fiber;Channels (ErrF == 0) / bin" % fedId)

    coords = (block["Crate"], block["Slot"], block["Top"], channelData["Fiber"], channelData["FibCh"])
    if coords in other.get("misMatched", []):
        nAdcMisMatch = 1
        crate2, slot2, top2 = hw.transformed_qie(*coords)[:3]
        for t in [slotCrate,
                  (slot2bin(slot2), crate2bin.get((crate2, top2), crateFail)),
                 ]:
            book.fill(t, "ADC_mismatch_vs_slot_crate", *misMatchMapBins,
                      title="ADC mismatch;slot;crate;Channels / bin",
                      yAxisLabels=yAxisLabels)
    elif coords in other.get("matched", []):
        nAdcMatch = 1

    caps[channelData["CapId0"]] += 1

    if channelData["QIE"]:
        adc = max(channelData["QIE"])
        adcs.add(adc)
        mp = channelData.get("M&P", 0)
        book.fill(adc, "channel_peak_adc_mp%d_%d" % (mp, fedId), 14, -0.5, 13.5,
                  title="FED %d;Peak ADC (ErrF == 0);Channels / bin" % fedId)

        if fedTime:
            histogramTsVsTime(book, fedTime, fedId, channelData["QIE"])
    return nAdcMatch, nAdcMisMatch


def histogramTsVsTime(book, fedTime, fedId, qies, adcMin=9, nBins=10):
    for i, adc in enumerate(qies):
        if adcMin <= adc:
            book.fill(i, "ts_qie_%d" % fedId, nBins, -0.5, nBins - 0.5,
                      title="FED %d;TS (when %s <= ADC);Channels / bin" % (fedId, adcMin))
            book.fill((fedTime/60., i), "ts_vs_time_%d" % fedId, (40, nBins), (0.0, -0.5), (4.0, nBins - 0.5),
                      title="FED %d;time (hours);TS (when %d <= ADC);Channels / bin" % (fedId, adcMin))


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
                if warn and d["utca"] and l[-1] in "CV":
                    printer.warning("%s / input %2d has bit %s set." % (msg, iHtr, l))


def singleFedPlots(fedId=None, d={}, book={}, **other):
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

    htrOverviewBits(h, book, fedId, msg=msg, warn=other["warn"])

    fedTime = utils.minutes(fedOrn, fedBcn)

    nBadHtrs, ErrF, caps, adcs, fracEvN, fracADC, fracTP = htrSummary(blocks=d["htrBlocks"].values(),
                                                                      book=book,
                                                                      fedId=fedId,
                                                                      fedEvn=fedEvn,
                                                                      fedOrn5=fedOrn & 0x1f,
                                                                      fedBcn=fedBcn,
                                                                      msg=msg,
                                                                      fedTime=fedTime,
                                                                      **other)

    errFSum = 0.0 + sum(ErrF.values())

    if errFSum:
        for code, n in ErrF.iteritems():
            title = "FED %d;frac. chan. with ErrF == %d;Events / bin" % (fedId, code)
            book.fill(n/errFSum, "ErrF%d_%d" % (code, fedId), 44, 0.0, 1.1, title=title)

        frac0 = ErrF[0] / errFSum
    else:
        frac0 = -999.  # dummy

    book.fillGraph((fedTime, frac0), "frac0_vs_time_%d" % fedId,
                   title=("FED %d" % fedId) +
                   ";time (minutes);frac. chan. with ErrF == 0")

    if fracEvN is not None:
        book.fillGraph((fedTime, fracEvN), "fracEvN_vs_time_%d" % fedId,
                       title=("FED %d" % fedId) +
                       ";time (minutes);frac. HTRs with EvN == FED's")

    if fracADC is not None:
        book.fillGraph((fedTime, fracADC), "ADC_misMatch_vs_time_%d" % fedId,
                       title=("FED %d" % fedId) +
                       ";time (minutes);#splitline{(# ch. match. ADCs) /}{(# ch. match. + ch. mismatch.)}")

    if fracTP is not None:
        book.fillGraph((fedTime, fracTP), "TP_misMatch_vs_time_%d" % fedId,
                       title=("FED %d" % fedId) +
                       ";time (minutes);#splitline{(# match. TPs) /}{(# match. + mismatch. TPs)}")

    if "nWord64" in t:
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


def checkHtrModules(fedId=None, spigots=[], htrBlocks={}):
    crates = []
    for iBlock, block in htrBlocks.iteritems():
        if block["IsTTP"]:
            continue

        expected = patterns.expectedHtr(fedId, spigots[iBlock])
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
        printer.warning("FED %s contains modules with crate labels %s." % (str(fedId), str(crates)))


def nPerChannel(lst=[], iChannel=None):
    return len(filter(lambda x: x[-1] == iChannel, lst))


def loop_over_feds(raw, book, adcTag="", **other):
    okFeds = set()
    adcs = set()

    for fedId, dct in sorted(raw.iteritems()):
        if fedId is None:
            continue

        book.fill(dct["nBytesSW"] / 1024.0, "nBytesSW_%d" % fedId, 64, 0, 64,
                  title="FED %d; kBytes;Events / bin" % fedId)

        fedIdHw = dct["header"]["FEDid"]
        if fedId != fedIdHw:
            printer.error("FED %d has FEDid %d" % (fedId, fedIdHw))
            continue

        nBadHtrs, adcs1 = singleFedPlots(fedId=fedId, d=dct, book=book, **other)
        adcs = adcs.union(adcs1)
        if nBadHtrs:
            return

        okFeds.add(fedId)
        if not raw[fedId]["header"]["utca"]:
            checkHtrModules(fedId=fedId,
                            spigots=spigotList(raw[fedId]["header"]),
                            htrBlocks=raw[fedId]["htrBlocks"])

    if adcs:
        book.fill(max(adcs), "max_adc_%s" % adcTag, 128, -0.5, 127.5,
                  title=";max ADC (when ErrF==0);Events / bin")

    return okFeds


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
                    print "iEntry %d: %s  |  %s  :  %s  |  %s" % (iEntry, c1, c2, q1, q2)
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

    titlePrefix = "ErrF == %s;ADC;ADC" % ",".join(["%d" % x for x in matching.okErrF()])
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


def histogram_deltas(raw1, raw2, book, okFeds):
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


def compare(raw1={}, raw2={}, book=None, anyEmap=False,  printEmap=False, printMismatches=False, warnQuality=True, fewerHistos=False):
    if raw2:
        if anyEmap:
            compare0(raw1, raw2, book, printEmap)
        else:
            compare1(raw1, raw2, book, printMismatches, warnQuality)

    okFeds = loop_over_feds(raw1, book, adcTag="feds1",
                            warn=warnQuality, fewerHistos=fewerHistos)

    noGood = [[], [None]]
    if raw1.keys() in noGood or raw2.keys() in noGood:
        return

    okFeds = okFeds.union(loop_over_feds(raw2, book, adcTag="feds2", warn=warnQuality))

    histogram_deltas(raw1, raw2, book, okFeds)


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


def matchStatsAnyMap(fIn={}, bIn={}, iStart=None):
    f = {}
    for coords, dataAll in fIn.iteritems():
        f[coords] = dataAll[iStart:]

    b = {}
    for dataAll, coords in bIn.iteritems():
        b[dataAll[iStart:]] = coords

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

                cap0 = channelData["CapId0"]
                data = tuple([nPre, delta, mp, cap0] + channelData["QIE"])
                # print coords, data
                forward[coords] = data
                backward[data] = coords
    return forward, backward, skipped


def tpMap(raw={}, warn=True, book=None):
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
