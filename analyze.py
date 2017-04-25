import os
import sys
import time
import utils

r = utils.ROOT()
import autoBook
from configuration import hw, sw, matching
import printer
import plugins
import raw


def import_plugins(names=[]):
    for p in names:
        exec("from plugins import %s" % p)


def coords(d):
    h = d["header"]
    return h["EvN"], h["OrN"], h["BcN"]


def chainLoopSparse(chain, nEntries, callback, nPerTree, progress=False):
    iMask = 0
    iTreeFirstEntry = 0
    nSeen = 0

    for nTree in range(chain.GetNtrees()):
        if chain.LoadTree(iTreeFirstEntry) < 0:
            return

        tree = chain.GetTree()
        if not tree:
            continue

        nTreeEntries = tree.GetEntries()
        for iTreeEntry in range(nTreeEntries):
            # if (not nTree) and iTreeEntry == 100:
            #     tree.StopCacheLearningPhase()

            if nPerTree <= iTreeEntry:
                break

            tree.GetEntry(iTreeEntry)  # fixme: protect?
            entry = iTreeFirstEntry + iTreeEntry
            nSeen += 1
            # print "nTree %d  iTreeEntry %d   entry %d   nSeen %d" % (nTree, iTreeEntry, entry, nSeen)

            if callback(chain, entry):
                return

            if progress:
                iMask = reportProgress(entry, nSeen, iMask)

            if nEntries != None and nEntries <= nSeen:
                return

        # tree.PrintCacheStats()
        iTreeFirstEntry += nTreeEntries


def chainLoop(chain, iEntryStart, iEntryStop, callback, progress=False, sparseLoop=None):
    if 0 <= sparseLoop:
        chainLoopSparse(chain, iEntryStop, callback, sparseLoop, progress=progress)
        return

    iMask = 0

    iEntry = iEntryStart
    while iEntry != iEntryStop:
        if chain.GetEntry(iEntry) <= 0:
            break
        if callback(chain, iEntry):
            break

        iEntry += 1
        if progress:
            iMask = reportProgress(iEntry, iEntry - iEntryStart, iMask)


def fillEventMap(iEntry, raw, forward, forwardBcn, backward):
    evn, orn, bcn = coords(raw)
    evnOrn = (evn, orn)

    forward[iEntry] = evnOrn
    forwardBcn[iEntry] = bcn
    backward[evnOrn] = iEntry


# this function returns two dictionaries,
# one maps TTree entry to (orn, evn)
# the other maps the reverse
def eventMaps(chain, s={}, identityMap=False):
    forward = {}
    backward = {}
    forwardBcn = {}

    if s["progress"]:
        print "Mapping %s:" % s["label"]

    try:
        def fillEventMap2(chain, iEntry):
            if iEntry == nMapMin:
                raw.pruneFeds(chain, s)

            return fillEventMap(iEntry, raw.unpackedHeader(s), forward, forwardBcn, backward)

        nMapMin = 0     # start from beginning
        nMapMax = None  # look at all entries

        nEv = s["nEventsMax"] + s["nEventsSkip"]
        if nEv:
            if identityMap:
                nMapMin = s["nEventsSkip"]
                nMapMax = nEv
            else:
                nMapMax = nEv * 2  # a guess for how far to look not to miss out-of-order events

        chainLoop(chain, nMapMin, nMapMax, fillEventMap2, progress=s["progress"], sparseLoop=s["sparseLoop"])
    except KeyboardInterrupt:
        printer.warning("KeyboardInterrupt in eventMaps()")

    return forward, backward, forwardBcn


def reportProgress(globalEntry, iEvent, iMask):
    if iEvent and not (iEvent & (2**iMask - 1)):
        msg = "%8d %s" % (iEvent, time.ctime())
        if globalEntry != iEvent:
            msg += "  (entry %8d)" % globalEntry
        print msg
        return iMask + 1
    else:
        return iMask


def outerInnerCompare(chain, oEntry, outer, inner, innerEvent, chainI, kargs):
    kargs["raw1"] = raw.collected(tree=chain, specs=outer)

    if innerEvent:
        iEntry = innerEvent[oEntry]
        if iEntry is None:
            oEntry += 1
            return

        if chainI.GetEntry(iEntry) <= 0:
            return True  # break!

    if inner:
        kargs["raw2"] = raw.collected(tree=chainI, specs=inner)

    if not outer["unpack"]:
        return

    for p in outer["plugins"]:
        f = getattr(eval("plugins.%s" % p), p)
        f(**kargs)


def loop(chain=None, chainI=None, outer={}, inner={}, innerEvent={}, options={}):
    if outer["progress"]:
        print "Looping:"

    kargs = {"book": autoBook.autoBook("book"),
             "warnQuality": outer["warnQuality"]}
    kargs.update(options)

    try:
        def outerInnerCompare2(chain, iEntry):
            return outerInnerCompare(chain, iEntry, outer, inner, innerEvent, chainI, kargs)

        nMin = outer["nEventsSkip"]
        nMax = (outer["nEventsSkip"] + outer["nEventsMax"]) if outer["nEventsMax"] else None
        chainLoop(chain, nMin, nMax, outerInnerCompare2,
                  progress=outer["progress"], sparseLoop=outer["sparseLoop"])

    except KeyboardInterrupt:
        printer.warning("KeyboardInterrupt in loop()")

    return kargs["book"]


def inner_vars(outer, inner, mapOptions, oMapF, oMapB, oMapBcn):
    if inner:
        chainI = raw.tchain(inner)
        iMapF, iMapB, iMapBcn = eventMaps(chainI, inner)
        if mapOptions["identityMap"]:
            iMapF = oMapF
            iMapB = oMapB
            iMapBcn = oMapBcn

        innerEvent = eventToEvent(oMapF, iMapB)
        if set(innerEvent.values()) == set([None]):
            sys.exit("No common events found.  Consider passing --identity-map.")

        if mapOptions['printEventMap']:
            for oEntry, iEntry in sorted(innerEvent.iteritems()):
                printer.msg(", ".join(["oEntry = %s" % str(oEntry),
                                       "oEvnOrn = %s" % str(oMapF[oEntry]),
                                       "iEntry = %s" % str(iEntry),
                                       ]))
    else:
        chainI = None
        innerEvent = iMapF = iMapB = iMapBcn = {}

    return chainI, innerEvent, iMapF, iMapB, iMapBcn


def category_vs_time(oMap={}, oMapBcn={}, iMap={}, iMapBcn={}, innerEvent={}):
    d = {}
    for oEntry, (evn, orn) in oMap.iteritems():
        bcn = oMapBcn[oEntry]
        time = hw.minutes(orn, bcn)
        if innerEvent.get(oEntry) is not None:
            d[time] = (3, evn, orn, bcn)
        else:
            d[time] = (2, evn, orn, bcn)

    iEntries = innerEvent.values()
    for iEntry, (evn, orn) in iMap.iteritems():
        if iEntry in iEntries:
            continue
        bcn = iMapBcn[iEntry]
        time = hw.minutes(orn, bcn)
        d[time] = (1, evn, orn, bcn)

    return d


def write_category_graphs(d={}, outer={}, inner={}):
    for iGraph, gr in enumerate(graphs(d, oFed=outer["fedId0"], iFed=inner.get("fedId0", None))):
        if iGraph == 0:
            gr.SetTitle("_".join(["only %s" % inner.get("label", ""), "only %s" % outer.get("label", ""), "both"]))
        if iGraph == 1:
            gr.SetTitle(",".join(outer["fileNames"]))
        gr.Write()


def graphs(d={}, oFed=None, iFed=None):
    gr1 = r.TGraph()
    gr2 = r.TGraph()
    gr3 = r.TGraph()
    gr4 = r.TGraph()

    suffix = ""
    for fed in [oFed, iFed]:
        if fed is not None:
            suffix += "_%d" % fed

    gr1.SetName("category_vs_time" + suffix)
    gr2.SetName("evn_vs_time" + suffix)
    gr3.SetName("bcn_delta_vs_time" + suffix)
    gr4.SetName("incr_evn_vs_time" + suffix)

    evn0 = orn0 = bcn0 = None
    for i, time in enumerate(sorted(d.keys())):
        category, evn, orn, bcn = d[time]
        gr1.SetPoint(i, time, category)
        gr2.SetPoint(i, time, evn)
        if orn0 is not None:
            gr3.SetPoint(i, time, hw.nBx * (orn - orn0) + (bcn - bcn0))
            gr4.SetPoint(i, time, evn0 < evn)
        else:
            gr3.SetPoint(i, time, 1.0e30)
            gr4.SetPoint(i, time, 1)
        evn0 = evn
        orn0 = orn
        bcn0 = bcn
    return gr1, gr2, gr3, gr4


def eventToEvent(mapF={}, mapB={}):
    out = {}
    for oEntry, evnOrn in mapF.iteritems():
        out[oEntry] = None
        if evnOrn in mapB:
            out[oEntry] = mapB[evnOrn]
    return out


def printEventSummary(outer, inner):
    if "compare" not in outer["plugins"]:
        return False
    if outer["dump"] < 0:
        return False
    if not inner:
        return False
    if outer["fileNames"] == inner["fileNames"]:
        return False
    return True


def go(outer={}, inner={}, outputFile="",
       mapOptions={}, options={}):

    raw.setup_root()
    import_plugins(outer["plugins"])
    outer.update(fileSpec(outer["fileNames"]))
    if inner:
        inner.update(fileSpec(inner["fileNames"]))
        if inner["fileNames"] == outer["fileNames"]:
            mapOptions["identityMap"] = True

    chain = raw.tchain(outer)
    oMapF, oMapB, oMapBcn = eventMaps(chain, outer, mapOptions["identityMap"])
    chainI, innerEvent, iMapF, iMapB, iMapBcn = inner_vars(outer, inner, mapOptions,
                                                           oMapF, oMapB, oMapBcn)
    book = loop(chain=chain, chainI=chainI,
                outer=outer, inner=inner,
                innerEvent=innerEvent,
                options=options)

    utils.delete(chain)
    if chainI:
        utils.delete(chainI)

    # write results to a ROOT file
    dirName = os.path.dirname(outputFile)
    if not os.path.exists(dirName):
        print "Creating directory '%s'" % dirName
        os.mkdir(dirName)

    f = r.TFile(outputFile, "RECREATE")
    if not f.IsZombie():
        write_category_graphs(category_vs_time(oMap=oMapF, oMapBcn=oMapBcn,
                                               iMap=iMapF, iMapBcn=iMapBcn,
                                               innerEvent=innerEvent),
                              outer,
                              inner)
        for h in book.values():
            h.Write()
    f.Close()

    for h in book.values():
        utils.delete(h)

    if printEventSummary(outer, inner):
        s = "%s: %4s = %6d" % (outputFile, outer["label"], len(oMapF))
        if inner:
            nBoth = len(filter(lambda x: x is not None, innerEvent.values()))
            s += ", %4s = %6d, both = %6d" % (inner["label"], len(iMapB), nBoth)
        printer.msg(s)

    oFeds = sorted(outer["wargs"].keys())
    iFeds = sorted(inner["wargs"].keys()) if inner else []
    return not len(oMapF), oFeds, iFeds


def printChannelSummary(outputFile):
    f = r.TFile(outputFile)

    hs = []
    for name in ["MatchedFibersCh%d" % i for i in range(3)] + ["MatchedTriggerTowers"]:
        h = f.Get(name)
        if h:
            hs.append(h)

    lines = []
    if hs:
        words = ["nMatched"]
        words += ["FibCh%d" % i for i in range(3)]
        words.append("  TPs")
        words = "   ".join(words)
        lines.append(words)
        lines.append("-" * len(words))
    else:
        return

    for iBin in range(0, 2 + hs[0].GetNbinsX()):
        xs = [h.GetBinCenter(iBin) for h in hs]
        if len(set(xs)) != 1:
            printer.error("binnings for nMatched do not match.")
            return

        for h in hs:
            w = h.GetBinWidth(iBin)
            if 1.0e-6 < abs(w - 1.0):
                printer.warning("Histogram %s bin %d has width %g" % (h.GetName(), iBin, w))

        x = xs[0]
        cs = [h.GetBinContent(iBin) for h in hs]

        if any(cs):
            s = ["   %4d" % x]
            s += ["%4d" % c for c in cs]
            lines.append("     ".join(s))

    if len(lines) > 12:
        printer.info("suppressed printing of match histogram (more than 10 different occupancies)")
    else:
        for line in lines:
            print line

    f.Close()


def bail(specs, fileName):
    n = max([len(spec["treeName"]) for spec in specs])
    fmt = "%" + str(n) + "s: %s\n"

    lst = []
    for spec in specs:
        name = spec["treeName"]
        del spec["treeName"]
        lst.append((name, spec))

    msg = "found %s != 1 known TTrees in file %s\n" % (len(specs), fileName)
    for name, spec in sorted(lst):
        msg += fmt % (name, str(spec))
    sys.exit(msg)


def fileSpec(fileString=""):
    fileNames = fileString.split(",")

    f = r.TFile.Open(fileNames[0])
    if (not f) or f.IsZombie():
        sys.exit("File %s could not be opened." % fileNames[0])

    treeNames = []
    for tkey in f.GetListOfKeys():
        obj = f.Get(tkey.GetName())
        if obj.ClassName() == "TTree":
            treeNames.append(obj.GetName())
    f.Close()

    specs = []
    for treeName in set(treeNames):  # set accomodate cycles, e.g. CMSRAW;3 CMSRAW;4
        spec = sw.format(treeName)
        if spec:
            spec["fileNames"] = fileNames
            spec["treeName"] = treeName
            specs.append(spec)

    if len(specs) != 1:
        bail(specs, fileName[0])
    else:
        return specs[0]


def subset(options, l, process=False, invert=False):
    assert not (process and invert)

    out = {}
    for item in l:
        value = getattr(options, item)
        if process:
            out[item] = fedList(value)
        elif invert:
            # "noFoo": True --> "foo": False
            out[item[2].lower() + item[3:]] = not value
        else:
            out[item] = value
    return out


def processed(options):
    if not all([options.file1, options.feds1]):
        sys.exit("--file1 and --feds1 are required (see './oneRun.py --help').")
    if not options.outputFile.endswith(".root"):
        sys.exit("--output-file must end with .root (%s)" % options.outputFile)
    if options.file2 and not options.feds2:
        sys.exit("--file2 requires --feds2")
    if 0 <= options.sparseLoop:
        if options.file2:
            sys.exit("--sparse-loop does not work with --file2")
        if options.nEventsSkip:
            sys.exit("--sparse-loop does not work with --nevents-skip")

    matching.__okErrF = sw.fedList(options.okErrF)
    matching.__utcaBcnDelta = options.utcaBcnDelta
    matching.__utcaPipelineDelta = options.utcaPipelineDelta
    printer.__color = not options.noColor

    common = subset(options, ["dump", "nEventsMax", "nEventsSkip", "progress", "sparseLoop"])
    common.update(subset(options, ["noUnpack", "noWarnQuality", "noWarnUnpack"], invert=True))
    common["crateslots"] = sw.fedList(options.crateslots)

    plugins = options.plugins.split(",")
    if 1 <= options.dump and "printraw" not in plugins:
        plugins.append("printraw")
    common["plugins"] = plugins

    outer = {"fedIds": sw.fedList(options.feds1),
             "label": "files1",
             "fileNames": options.file1}
    outer.update(common)

    inner = {}
    if options.feds2:
        inner = {"fedIds": sw.fedList(options.feds2),
                 "label": "files2",
                 "fileNames": options.file2 if options.file2 else options.file1}
        inner.update(common)

    return {"outer": outer,
            "inner": inner,
            "outputFile": options.outputFile,
            "mapOptions": subset(options, ["printEventMap", "identityMap"]),
            "options": subset(options, ["anyEmap", "printEmap", "printMismatches", "fewerHistos"])}


def main(options):
    kargs = processed(options)
    return go(**kargs)
