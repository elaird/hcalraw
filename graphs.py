import math
import collections
import printer
import utils
r = utils.ROOT()


def combineBinContentAndError(histo, binToContainCombo, binToBeKilled):
    xflows     = histo.GetBinContent(binToBeKilled)
    xflowError = histo.GetBinError(binToBeKilled)

    if xflows == 0.0:  # ugly
        return

    currentContent = histo.GetBinContent(binToContainCombo)
    currentError   = histo.GetBinError(binToContainCombo)

    histo.SetBinContent(binToBeKilled, 0.0)
    histo.SetBinContent(binToContainCombo, currentContent+xflows)

    histo.SetBinError(binToBeKilled, 0.0)
    histo.SetBinError(binToContainCombo, math.sqrt(xflowError**2+currentError**2))


def shiftFlows(histo=None):
    bins = histo.GetNbinsX()
    entries = histo.GetEntries()
    combineBinContentAndError(histo, binToContainCombo=1   , binToBeKilled=0     )
    combineBinContentAndError(histo, binToContainCombo=bins, binToBeKilled=bins+1)
    histo.SetEntries(entries)


def labelYAxis(h=None, labels={}):
    h.SetStats(False)
    yaxis = h.GetYaxis()
    for iBin, label in sorted(labels.iteritems()):
        yaxis.SetBinLabel(iBin, label)
    yaxis.SetLabelSize(2.0 * 0.035)


def xMin_xMax(graph=None):
    """assumes that graph is sorted"""
    N = graph.GetN()
    X = graph.GetX()
    if 1 <= N:
        return X[0], X[N-1]
    else:
        printer.error("graph contains zero points.")
        return 0.0, 0.0


def multiY(graph=None):
    s = set()
    y = graph.GetY()
    for i in range(graph.GetN()):
        s.add(y[i])
    return 2 <= len(s)


def fillRateHisto(h, g):
    x = g.GetX()
    y = g.GetY()
    evn = collections.defaultdict(list)
    for i in range(g.GetN()):
        iBin = h.FindBin(x[i])
        evn[iBin].append(y[i])

    for iBin, lst in evn.iteritems():
        nL1A = 1 + max(lst) - min(lst)
        deltaT = h.GetBinWidth(iBin)  # minutes
        deltaT *= 60.0  # seconds
        c = nL1A / deltaT
        h.SetBinContent(iBin, c)

        relErr = 1.0 / len(lst)  # +- 1 events
        h.SetBinError(iBin, c * relErr)


def magnify(h, factor=1.0):
    h.GetYaxis().SetTitleOffset(1.2)
    h.GetZaxis().SetTitleOffset(1.2)

    default = 0.035
    for axis in [h.GetXaxis(), h.GetYaxis(), h.GetZaxis()][:2]:
        axis.SetLabelSize(factor * default)
        axis.SetTitleSize(factor * default)



def adjustPad(pad=r.gPad, logX=False, logY=False, logZ=False,
              m={"Left": 0.15, "Bottom": 0.15, "Right": 0.15, "Top": None}):

    for key, value in m.iteritems():
        if value is None:
            continue
        getattr(r.gPad, "Set%sMargin" % key)(value)

    r.gPad.SetTickx()
    r.gPad.SetTicky()
    if logX:
        r.gPad.SetLogx()
    if logY:
        r.gPad.SetLogy()
    if logZ:
        r.gPad.SetLogz()


def stylize(h, color=r.kBlack, style=1, width=1):
    #r.gStyle.SetOptStat(110010)
    h.SetStats(False)
    h.SetMinimum(0.5)
    h.SetLineColor(color)
    h.SetLineStyle(style)
    h.SetLineWidth(width)


def legends(legEntries=[]):
    out = []
    dx = 0.8/max(1, len(legEntries))
    x0 = 0.1
    for iLeg, (h, desc) in enumerate(legEntries):
        leg = r.TLegend(x0, 0.91, x0+dx, 1.0)
        x0 += dx
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.AddEntry(h, desc, "l")
        leg.Draw()
        out.append(leg)
    return out


def justOne(s):
    fields = s.split("_")
    return 2 <= len(fields) and fields[0] == "BcN" and fields[1] != "HTRs"


def histoLoop(f, lst, func):
    out = []
    maxes = []
    legEntries = []
    h0 = None

    didOne = False
    for x, color, style in lst:
        h = f.Get(func(x))
        if not h:
            continue

        if not h.GetEntries():
            continue

        if justOne(func(x)):
            if didOne:
                continue
            didOne = True

        gopts = "hist"
        if h0:
            gopts += "same"
        else:
            h0 = h
        maxes.append(h.GetMaximum())
        shiftFlows(h)
        h.Draw(gopts)
        stylize(h, color, style)
        magnify(h, factor=1.8)
        out.append(h)

        s = "MatchedFibers"
        if func(x).startswith(s):
            ch = func(x).replace(s, "")[-1]
            #t = "#splitline{%s}{%s}" % ("Ch " + ch, "%d#pm%d" % (h.GetMean(), h.GetRMS()))
            t = "Ch%s  (%d#pm%d)" % (ch, h.GetMean(), h.GetRMS())
            h.GetXaxis().SetTitle(h.GetXaxis().GetTitle()[:-6])
        elif func(x).startswith("MatchedTriggerTowers"):
            t = "%d#pm%d" % (h.GetMean(), h.GetRMS())
        else:
            t = h.GetTitle().replace("FED ", "")

        if justOne(func(x)):
            t += "   (%d entries)" % h.GetEntries()

        legEntries.append((h, t))
        h.SetTitle("")

    if maxes and h0:
        h0.SetMaximum(2.0*max(maxes))
    out += legends(legEntries)
    return out


def fedString(lst=[]):
    return ",".join(["%d" % i for i in lst])


def plotGlobal(f, pad, offset=None, names=[], logY=False, logX=False, logZ=True, gopts="colz", feds1=[], feds2=[]):
    keep = []

    for iHisto, name in enumerate(names):
        if not name:
            continue
        pad.cd(offset + iHisto)
        adjustPad(logX=logX, logY=logY, logZ=logZ)
        h = f.Get(name)
        if not h:
            print "ERROR: could not find histogram %s." % name
            continue

        shiftFlows(h)
        h.Draw(gopts)
        stylize(h)
        magnify(h, factor=1.8)

        P = name[:name.find("_vs_")].upper()
        h.GetXaxis().SetTitle("%s (%s)" % (P, fedString(feds1)))
        h.GetYaxis().SetTitle("%s (%s)" % (P, fedString(feds2)))
        h.GetZaxis().SetTitle("samples / bin")

        yx = r.TF1("yx", "x", h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax())
        yx.SetLineColor(r.kBlack)
        yx.SetLineWidth(1)
        yx.SetLineStyle(3)
        yx.Draw("same")

        leg = r.TLegend(0.2, 0.75, 0.5, 0.85)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.AddEntry(yx, "y = x", "l")
        leg.Draw()
        keep += [h, yx, leg]
    return keep


def plotList(f, pad, offset=None, names=[], logY=True, logX=False, logZ=False, gopts="hist", feds1=[], feds2=[]):
    fedList = (feds1 + feds2)[:5]
    color = [r.kBlack, r.kRed, r.kBlue, r.kGreen, r.kMagenta]
    color += [r.kBlack] * (len(fedList) - len(color))
    style = [1, 2, 3, 4, 5]
    style += [1] * (len(fedList) - len(style))

    keep = []
    for iHisto, name in enumerate(names):
        if not name:
            continue
        pad.cd(offset + iHisto)
        adjustPad(logX=logX, logY=logY, logZ=logZ)

        feds = []
        for iFed, fed in enumerate(sorted(fedList)):
            feds.append((fed, color[iFed], style[iFed]))

        keep += histoLoop(f, feds, lambda x: "%s_%d" % (name, x))
    return keep


def draw_graph(graph, pad1, title="", rate=False):
    if not graph:
        return

    graph.SetMarkerStyle(20)
    graph.SetMarkerColor(r.gStyle.GetHistLineColor())
    graph.SetMarkerSize(0.5*graph.GetMarkerSize())
    t = graph.GetTitle().split("_")

    pad1.cd()
    if rate:
        adjustPad(m={"Bottom": 0.2, "Left": 0.1, "Top": 0.2, "Right": 0.0})
    else:
        adjustPad(m={"Left": 0.2, "Bottom": 0.2, "Right": None, "Top": None})

    xMin, xMax = xMin_xMax(graph)
    delta = xMax - xMin
    if delta:
        tenPercent = 0.1 * delta
    else:
        tenPercent = 0.1/60.0  # 1/10 second

    null = r.TH2D("null", "%s;time (minutes)" % title,
                  60, xMin - tenPercent, xMax + tenPercent,
                  3, 0.5, 3.5)

    if rate:
        h = null.ProjectionX()
        fillRateHisto(h, graph)
        h.SetStats(False)
        h.Draw()
        h.SetMinimum(5.0e1)
        h.SetMaximum(2.0e5)
        h.GetYaxis().SetTitle("L1A rate (Hz)")
        r.gPad.SetLogy()
        r.gPad.SetGridy()
    else:
        h = null
        h.Draw()
        labelYAxis(h, labels={1: t[0], 2: t[1], 3: t[2]})
        graph.Draw("psame")

    magnify(h, factor=3.0)
    h.GetXaxis().SetTitleOffset(0.75)
    h.GetYaxis().SetTitleOffset(0.4)
    return graph, h


def pageOne(f=None, feds1=[], feds2=[], canvas=None, pdf=""):
    pad1 = r.TPad("pad1", "pad1", 0.00, 0.75, 0.75, 1.00)
    pad2 = r.TPad("pad2", "pad2", 0.00, 0.00, 1.00, 1.00)

    pad2.Divide(5, 4, 0.001, 0.001)
    pad2.Draw()
    pad1.Draw()

    keep = []

    # category/rate graph
    r.gStyle.SetTitleBorderSize(0)
    r.gStyle.SetTitleX(0.53)
    r.gStyle.SetTitleY(0.9)
    r.gStyle.SetTitleFontSize(0.12)
    r.gStyle.SetTitleAlign(22)

    title = f.GetPath()
    cats = f.Get("category_vs_time")
    if multiY(cats):
        keep += draw_graph(cats, pad1, title)
    else:
        keep += draw_graph(f.Get("evn_vs_time"), pad1, title, rate=True)


    # single FED
    keep += plotList(f, pad2, offset=5,
                     names=["BcN",
                            "nBytesSW", "nWord16Skipped", "ChannelFlavor", "nQieSamples", "ErrF0",
                            "EvN_HTRs", "OrN5_HTRs", "BcN_HTRs", "LMSEPVC", "TTS",
                            # "PopCapFrac",
                            ], feds1=feds1, feds2=feds2)

    # EvN, OrN, BcN agreement
    fed1 = sorted(feds1)[0]
    for i, fed2 in enumerate(feds2[:3]):
        pad2.cd(16 + i)
        adjustPad(logY=True)
        keep += histoLoop(f,
                          [("OrN", r.kBlue, 1),
                           ("EvN", r.kCyan, 2),
                           ("BcN", r.kBlack, 3),
                           ],
                          lambda x: "delta%s_%s_%s" % (x, fed1, fed2),
                          )

    # fibers
    pad2.cd(19)
    adjustPad(logY=True)
    keep += histoLoop(f,
                      [("MatchedFibersCh0", r.kBlue, 1),
                       ("MatchedFibersCh1", r.kCyan, 2),
                       ("MatchedFibersCh2", r.kBlack, 3),
                       ],
                      lambda x: x,
                      )

    # tps
    pad2.cd(20)
    adjustPad(logY=True)
    keep += histoLoop(f, [("MatchedTriggerTowers", r.kBlack, 1)], lambda x: x)

    canvas.Print(pdf)


def pageTwo(f=None, feds1=[], feds2=[], canvas=None, pdf=""):
    pad0 = r.TPad("pad0", "pad0", 0.00, 0.00, 1.00, 1.00)
    pad0.Divide(2, 1)
    pad0.Draw()

    keep = plotGlobal(f, pad0, offset=1, names=["adc_vs_adc", "tp_vs_tp"], feds1=feds1, feds2=feds2)
    canvas.Print(pdf)


def makeSummaryPdf(inputFiles=[], feds1=[], feds2=[], pdf="summary.pdf", scatter=False):
    r.gROOT.SetBatch(True)
    r.gROOT.SetStyle("Plain")
    r.gErrorIgnoreLevel = r.kWarning

    canvas = r.TCanvas()
    canvas.Print(pdf + "[")

    for fileName in inputFiles:
        f = r.TFile(fileName)
        if (not f) or f.IsZombie():
            continue

        pageOne(f, feds1, feds2, canvas, pdf)
        if feds2:
            canvas.cd(0)
            pageTwo(f, feds1, feds2, canvas, pdf)

        f.Close()
    canvas.Print(pdf + "]")

    if scatter:
        import adc_vs_adc
        for prefix in ["adc_vs_adc", "tp_vs_tp"]:
            adc_vs_adc.go(fileName=inputFiles[0], feds1=feds1, feds2=feds2, prefix=prefix)
