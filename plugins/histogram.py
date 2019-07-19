import collections
from configuration import hw, sw
from plugins.eventtype import SetupType
import printer


def histogram(raw1={}, raw2={}, book=None, warnQuality=True, fewerHistos=False, **_):
    for i, raw in enumerate([raw1, raw2]):
        if not raw:
            continue
        loop_over_feds(raw, book, adcTag="feds%d" % (1 + i), warn=warnQuality, fewerHistos=fewerHistos)


def loop_over_feds(raw, book, adcTag="", **other):
    okFeds = set()
    adcs = set()

    nTsMax = raw[None]["firstNTs"]
    keys2 = [x for x in raw if x is not None]
    for fedId in sorted(keys2):
        dct = raw[fedId]

        book.fill(dct["nBytesSW"] / 1024.0, "nBytesSW_%d" % fedId, 64, 0, 32,
                  title="FED %d; kBytes;Events / bin" % fedId)

        fedIdHw = dct["header"]["FEDid"]
        if fedId != fedIdHw:
            printer.error("FED %d has FEDid %d" % (fedId, fedIdHw))
            continue

        if "htrBlocks" not in dct:
            continue

        nBadHtrs, adcs1 = singleFedPlots(fedId=fedId, d=dct, book=book, nTsMax=nTsMax, **other)
        adcs = adcs.union(adcs1)
        if nBadHtrs:
            return

        okFeds.add(fedId)
        h = raw[fedId]["header"]
        if not h["utca"]:
            checkHtrModules(fedId=fedId,
                            spigots=h["spigotList"],
                            htrBlocks=raw[fedId]["htrBlocks"])

    if adcs:
        book.fill(max(adcs), "max_adc_%s" % adcTag, 128, -0.5, 127.5,
                  title=";max ADC (when ErrF==0);Events / bin")

    return okFeds


def singleFedPlots(fedId=None, d={}, book={}, nTsMax=None, **other):
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
        printer.error("%s lacks EvN.  Keys: %s" % (msg, str(h.keys())))
        msg = ""
    else:
        msg = msg_coords(fedId, fedEvn, fedOrn, fedBcn)

    htrOverviewBits(h, book, fedId, msg=msg, warn=other["warn"])

    fedTime = hw.minutes(fedOrn, fedBcn)

    nBadHtrs, ErrF, caps, adcs, fracEvN, fracADC, fracTP = htrSummary(blocks=d["htrBlocks"].values(),
                                                                      book=book,
                                                                      fedId=fedId,
                                                                      fedEvn=fedEvn,
                                                                      fedOrn5=fedOrn & 0x1f,
                                                                      fedBcn=fedBcn,
                                                                      msg=msg,
                                                                      fedTime=fedTime,
                                                                      nTsMax=nTsMax,
                                                                      **other)

    errFSum = 0.0 + sum(ErrF.values())

    if errFSum:
        for code, n in ErrF.items():
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
    for iBlock, block in htrBlocks.items():
        if block["IsTTP"]:
            continue

        spigot = spigots[iBlock]
        expected = hw.expectedVmeHtr(fedId, spigot)
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


def msg_coords(fedId, evn, orn, bcn):
    return "FED %4d / EvN 0x%06x (OrN 0x%08x BcN %04d)" % (fedId, evn, orn, bcn)


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


def htrSummary(blocks=[], book=None, fedId=None,
               fedEvn=None, fedOrn5=None, fedBcn=None,
               msg="", warn=True, fewerHistos=False,
               fedTime=None, nTsMax=None,
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

    crate2bin = collections.defaultdict(int)
    yAxisLabels = ["?"]

    for iCrate, crate in enumerate(sw.crateList()):
        crate2bin[crate] = 1 + iCrate
        yAxisLabels.append("%2d" % crate)

    nSlots = 21
    xAxisLabels = ["%d" % s for s in range(1, 1 + nSlots)]
    x0 =  0.5
    y0 = -0.5
    nCrates = len(yAxisLabels)
    misMatchMapBins = ((nSlots, nCrates), (x0, y0), (x0 + nSlots, y0 + nCrates))

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
        slotCrate = (block["Slot"], crate2bin[block["Crate"]])
        histogramBlock2(book, block, fedEvn, fedOrn5, fedBcn, slotCrate, misMatchMapBins, xAxisLabels, yAxisLabels)

        nTpTowerBins = 50
        book.fill(len(block["triggerData"]), "nTpTowers_%d" % fedId, nTpTowerBins, -0.5, nTpTowerBins - 0.5,
                  title="FED %d;number of TP towers;HTRs / bin" % fedId)

        nChannelBins = 75
        book.fill(len(block["channelData"]), "nChannels_%d" % fedId, nChannelBins, -0.5, 2*nChannelBins - 0.5,
                  title="FED %d;number of channels;HTRs / bin" % fedId)

        if fewerHistos:
            continue

        if block["IsIO"]:
            nBins = 16
            book.fill(block["EventType"], "uMNioEventType_%d" % fedId, nBins, -0.5, nBins - 0.5,
                      title="FED %d;event type;uMNios / bin" % fedId)
            if block["EventType"] == 14:  # laser
                nBins = len(SetupType)
                book.fill(block["UserWords"][16], "uMNioUserValue16_%d" % fedId, nBins, -1.5, nBins - 1.5,
                          title="FED %d;user value (key=16);uMNios / bin" % fedId, xAxisLabels=SetupType)

        for otherData in block["otherData"].values():
            flavor(book, otherData, fedId)

        for techData in block["technicalData"].values():
            # remove uHTR pad words from flavor histogram
            if techData["technicalDataType"] or techData["channelId"] or techData["words"]:
                flavor(book, techData, fedId)

        for triggerKey, triggerData in block["triggerData"].items():
            if "Flavor" in triggerData:
                flavor(book, triggerData, fedId)

            tpMatch = histogramTriggerData(book, block, triggerData, triggerKey, fedId,
                                           crate2bin, slotCrate,
                                           misMatchMapBins, xAxisLabels, yAxisLabels,
                                           tpMatches=other.get("tMatched", []), # tpMismatches,
                                          )
            if tpMatch:
                nTpMatch += 1
            else:
                nTpMisMatch += 1

        for channelData in block["channelData"].values():
            flavor(book, channelData, fedId)
            a, b = histogramChannelData(book, block, channelData, fedId, caps, ErrF, adcs,
                                        crate2bin, slotCrate,
                                        misMatchMapBins, xAxisLabels, yAxisLabels,
                                        fedTime, nTsMax, warn, **other)
            nAdcMatch += a
            nAdcMisMatch += b

    return [nBadHtrs, ErrF, caps, adcs,
            matchFrac(nEvnMatch, nEvnMisMatch),
            matchFrac(nAdcMatch, nAdcMisMatch),
            matchFrac(nTpMatch, nTpMisMatch),
            ]


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


def histogramBlock2(book, block, fedEvn, fedOrn5, fedBcn, slotCrate, misMatchMapBins, xAxisLabels, yAxisLabels):
    book.fill(slotCrate,
              "block_vs_slot_crate",
              *misMatchMapBins,
              title="any;slot;crate;HTR / bin",
              xAxisLabels=xAxisLabels, yAxisLabels=yAxisLabels)

    for key, fedVar in [("EvN", fedEvn),
                        ("OrN5", fedOrn5),
                        ("BcN", fedBcn),
                         ]:
        if (block[key] - fedVar):
            book.fill(slotCrate,
                      "%s_mismatch_vs_slot_crate" % key,
                      *misMatchMapBins,
                      title="%s mismatch;slot;crate;HTR - FED   mismatches / bin" % key,
                      xAxisLabels=xAxisLabels, yAxisLabels=yAxisLabels)


def matchFrac(nMatch, nMisMatch):
    total = nMatch + nMisMatch
    if total:
        return (0.0 + nMatch) / total
    else:
        return None


def flavor(book, d, fedId):
    x = d["Flavor"]
    if x == 0:
        x = 1
    book.fill(x, "ChannelFlavor_%d" % fedId, 7, 0.5, 7.5,
              title="FED %d;channel flavor;Channels / bin" % fedId,
              xAxisLabels=["HE", "HF", "HB", "uTP", "Q5", "Q6", "7"])


def histogramTriggerData(book, block, triggerData, triggerKey, fedId,
                         crate2bin, slotCrate, misMatchMapBins, xAxisLabels, yAxisLabels,
                         tpMatches=None, # tpMismatches,
                         ):

    book.fill(len(triggerData["TP"]), "nTpSamples_%d" % fedId, 14, -0.5, 13.5,
              title="FED %d;number of TP samples;Towers / bin" % fedId)

    book.fill(slotCrate, "TP_vs_slot_crate", *misMatchMapBins,
              title="TP present;slot;crate;Towers / bin",
              xAxisLabels=xAxisLabels, yAxisLabels=yAxisLabels)

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
                  xAxisLabels=xAxisLabels, yAxisLabels=yAxisLabels)
        return

    crate2, slot2, top2 = tpCoords2[:3]
    slotsCrates = [slotCrate,
                   (slot2, crate2bin[crate2]),
                   ]

    for t in slotsCrates:
        book.fill(t, "TP_matchable_vs_slot_crate", *misMatchMapBins,
                  title="TP matchable;slot;crate;Towers / bin",
                  xAxisLabels=xAxisLabels, yAxisLabels=yAxisLabels)

    if tpCoords in tpMatches:
        return True
    else:
        for t in slotsCrates:
            book.fill(t, "TP_mismatch_vs_slot_crate", *misMatchMapBins,
                      title="TP mismatch;slot;crate;Towers / bin",
                      xAxisLabels=xAxisLabels, yAxisLabels=yAxisLabels)
        return False


def histogramChannelData(book, block, channelData, fedId,
                         caps, ErrF, adcs, crate2bin,
                         slotCrate, misMatchMapBins,
                         xAxisLabels, yAxisLabels, fedTime, nTsMax,
                         warn, **other):

    nAdcMatch = 0
    nAdcMisMatch = 0

    ErrF[channelData["ErrF"]] += 1
    book.fill(len(channelData["QIE"]), "nQieSamples_%d" % fedId, 14, -0.5, 13.5,
              title="FED %d;number of QIE samples;Channels / bin" % fedId)

    book.fill(slotCrate,
              "ErrFAny_vs_slot_crate", *misMatchMapBins,
              title="any;slot;crate;Channels / bin",
              xAxisLabels=xAxisLabels, yAxisLabels=yAxisLabels)

    if channelData["ErrF"]:
        for name, title in [("ErrFNZ", "ErrF != 0"),
                            ("ErrF%d" % channelData["ErrF"], "ErrF == %d" % channelData["ErrF"]),
                            ]:
            book.fill(slotCrate,
                      "%s_vs_slot_crate" % name, *misMatchMapBins,
                      title="%s;slot;crate;Channels / bin" % title,
                      xAxisLabels=xAxisLabels, yAxisLabels=yAxisLabels)
        return nAdcMatch, nAdcMisMatch

    book.fill(slotCrate,
              "ErrF0_vs_slot_crate", *misMatchMapBins,
              title="ErrF == 0;slot;crate;Channels / bin",
              xAxisLabels=xAxisLabels, yAxisLabels=yAxisLabels)

    book.fill((block["Slot"], channelData["Fiber"]),
              "fiber_vs_slot_%d" % fedId, (12, 24), (0.5, -0.5), (12.5, 23.5),
              title="FED %d;Slot;Fiber;Channels (ErrF == 0) / bin" % fedId)

    coords = (block["Crate"], block["Slot"], block["Top"], channelData["Fiber"], channelData["FibCh"])
    if coords in other.get("misMatched", []):
        nAdcMisMatch = 1
        crate2, slot2, top2 = hw.transformed_qie(*coords)[:3]
        for t in [slotCrate, (slot2, crate2bin[crate2])]:
            book.fill(t, "ADC_mismatch_vs_slot_crate", *misMatchMapBins,
                      title="ADC mismatch;slot;crate;Channels / bin",
                      xAxisLabels=xAxisLabels, yAxisLabels=yAxisLabels)
    elif coords in other.get("matched", []):
        nAdcMatch = 1

    if channelData["CapId"]:
        caps[channelData["CapId"][0]] += 1

    try:
        tsSoi = channelData["SOI"].index(1)
    except ValueError:
        if warn:
            printer.warning("%2d:%2d:%2d:%d SoI not found" % (block["Crate"], block["Slot"], channelData["Fiber"], channelData["FibCh"]))
        tsSoi = None

    if channelData["QIE"]:
        errf = "ErrFNZ" if channelData["ErrF"] else "ErrF0"
        eq = "!=" if channelData["ErrF"] else "=="

        histogramAdcs(book, fedId, block, channelData, adcs, nTsMax, errf, eq)
        histogramCaps(book, fedId, block, channelData["CapId"], tsSoi)
        if fedTime:
            histogramTsVsTime(book, fedTime, fedId, channelData["QIE"])

    if channelData.get("TDC"):
        histogramTdcs(book, fedId, block, channelData["TDC"], nTsMax, errf, eq, tsSoi)

    return nAdcMatch, nAdcMisMatch


def histogramCaps(book, fedId, block, caps, tsSoi, nCaps=4):
    if tsSoi is None:
        return

    if tsSoi < len(caps):
        capSoi = caps[tsSoi]
    else:
        capSoi = caps[0] + tsSoi

    book.fill((capSoi - block["BcN"]) % nCaps,
              "CapIdSoiMinusBcn_%d" % fedId,
              nCaps, -0.5, nCaps - 0.5,
              title="FED %d;(CapIdSoI - BcN) %s 4;Counts / bin" % (fedId, "%"))


def histogramAdcs(book, fedId, block, channelData, adcs, nTsMax, errf, eq):
    nAdcMax = 256

    adc = max(channelData["QIE"])
    adcs.add(adc)
    mp = channelData.get("M&P", 0)
    book.fill(adc, "channel_peak_adc_mp%d_%d" % (mp, fedId), nAdcMax, -0.5, nAdcMax - 0.5,
              title="FED %d;Peak ADC (ErrF == 0);Channels / bin" % fedId)


    for (i, adc) in enumerate(channelData["QIE"]):
        if nTsMax <= i:
            break

        book.fill((i, adc), "ADC_vs_TS_%s_%d" % (errf, fedId),
                  (nTsMax, nAdcMax), (-0.5, -0.5), (nTsMax - 0.5, nAdcMax - 0.5),
                  title="FED %d (ErrF %s 0);time slice;ADC;Counts / bin" % (fedId, eq))

        if block["Crate"] != 34: # sectors 16/17
            continue

        label = ""
        fib = 0
        if block["Slot"] == 7:  # HBP16
            label = "HBP16"
            fib = channelData["Fiber"]
        elif block["Slot"] == 8 and 2 <= channelData["Fiber"] <= 11:  # HBP16
            label = "HBP16"
            fib = 24 + channelData["Fiber"] - 2
        elif block["Slot"] == 12:  # HEP17
            label = "HEP17"
            if channelData["Fiber"] % 12 == 11:  # CU fibers
                fib = 32 + channelData["Fiber"] / 12
            else:
                fib += 12 + channelData["Fiber"] - 1
                if 13 <= channelData["Fiber"]:
                    fib -= 2
        elif block["Slot"] == 11 and 12 <= channelData["Fiber"]:  # HEP17
            label = "HEP17"
            fib += channelData["Fiber"] - 12
        else:
            continue

        # if (2 <= channelData["Flavor"]) and (not channelData["ErrF"]):
        #     printer.warning("Crate %d Slot %d Fib %d Channel %d has flavor %d" % \
        #                     (block["Crate"], block["Slot"], channelData["Fiber"], channelData["FibCh"], channelData["Flavor"]))

        book.fill((i, adc),
                  "ADC_vs_TS_%s_%s_fib%d" % (label, errf, fib),
                  (nTsMax, nAdcMax), (-0.5, -0.5), (nTsMax - 0.5, nAdcMax - 0.5),
                  title="%s Fib %d;time slice;ADC;Counts / bin" % (label, fib))
        book.fill(adc,
                  "%s_ADC_TS%d" % (label, i),
                  nAdcMax, -0.5, nAdcMax - 0.5,
                  title="%s TS%d;ADC;Counts / bin" % (label, i))

        # nEvN = 20
        # title2 = "%s_vs_EvN_%d" % (title, fedId)
        # book.fill((block["EvN"], adc), title2,
        #           (nEvN, 256), (0.5, -0.5), (nEvN + 0.5, 255.5),
        #           title="%s;EvN;ADC;Counts / bin" % title2)


def histogramTdcs(book, fedId, block, tdcs, nTsMax, errf, eq, tsSoi):
    tdcMax = 64

    for (i, tdc) in enumerate(tdcs):
        if nTsMax <= i:
            break

        book.fill((i, tdc), "TDC_vs_TS_%s_%d" % (errf, fedId),
                  (nTsMax, tdcMax), (-0.5, -0.5), (nTsMax - 0.5, tdcMax - 0.5),
                  title="FED %d (ErrF %s 0);time slice;TDC;Counts / bin" % (fedId, eq))

        if tdc < 50 and tsSoi is not None:
            t = 25.0 * (i - tsSoi) + tdc / 2.0
            book.fill(t, "TDCHitTime_%d" % fedId, 110, -55.0, 55.0,
                      title="FED %d;TDC hit time w.r.t. SoI (ns);Counts / bin" % fedId)

            # nEvN = 1000
            # book.fill((block["EvN"], t),
            #           "TDCHitTime_vs_EvN_%d" % fedId,
            #           (nEvN, 110), (0.5, -55.0), (nEvN + 0.5, 55.0),
            #           title="FED %d;EvN;TDC hit time w.r.t. SoI (ns);Counts / bin" % fedId)


def histogramTsVsTime(book, fedTime, fedId, qies, adcMin=16, nBins=10):
    for i, adc in enumerate(qies):
        if adcMin <= adc:
            book.fill(i, "ts_qie_%d" % fedId, nBins, -0.5, nBins - 0.5,
                      title="FED %d;TS (when %s <= ADC);Channels / bin" % (fedId, adcMin))
            book.fill((fedTime/60., i), "ts_vs_time_%d" % fedId, (40, nBins), (0.0, -0.5), (4.0, nBins - 0.5),
                      title="FED %d;time (hours);TS (when %d <= ADC);Channels / bin" % (fedId, adcMin))


