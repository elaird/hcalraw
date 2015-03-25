import math
import collections
import configuration
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


def labelXAxis(h=None, labels={}):
    h.SetStats(False)
    axis = h.GetXaxis()
    for iBin in range(1, 1 + axis.GetNbins()):
        x = int(axis.GetBinCenter(iBin))
        axis.SetBinLabel(iBin, labels.get(x, "%d" % x))
    axis.SetLabelSize(1.5*axis.GetLabelSize())
    axis.SetLabelOffset(1.5*axis.GetLabelOffset())


def labelYAxis(h=None, labels={}):
    h.SetStats(False)
    yaxis = h.GetYaxis()
    for iBin, label in sorted(labels.iteritems()):
        yaxis.SetBinLabel(iBin, label)
    yaxis.SetLabelSize(2.0*yaxis.GetLabelSize())


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

    for axis in [h.GetXaxis(), h.GetYaxis(), h.GetZaxis()][:2]:
        axis.SetLabelSize(factor*axis.GetLabelSize())
        axis.SetTitleSize(factor*axis.GetTitleSize())



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
    magnify(h, factor=1.8)
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


def histoLoop(f, lst, func):
    out = []
    maxes = []
    legEntries = []
    h0 = None

    for i, (x, color, style) in enumerate(lst):
        h = f.Get(func(x))
        if not h:
            continue

        if not h.GetEntries():
            continue

        if h.GetName().startswith("ChannelFlavor"):
            labelXAxis(h, labels=configuration.flavorLabels())

        gopts = "hist"
        if h0:
            gopts += "same"
        else:
            h0 = h
        maxes.append(h.GetMaximum())
        shiftFlows(h)
        h.Draw(gopts)
        stylize(h, color, style)
        out.append(h)

        s = "MatchedFibers"
        if func(x).startswith(s):
            ch = func(x).replace(s, "")[-1]
            #t = "#splitline{%s}{%s}" % ("Ch " + ch, "%d#pm%d" % (h.GetMean(), h.GetRMS()))
            t = "Ch%s  (%d#pm%d)" % (ch, h.GetMean(), h.GetRMS())
            h.GetXaxis().SetTitle(h.GetXaxis().GetTitle()[:-6])
        else:
            t = h.GetTitle().replace("FED ", "")

        if len(lst) == 1 and  func(x).startswith("BcN"):
            t += "   (%d entries)" % h.GetEntries()

        legEntries.append((h, t))
        h.SetTitle("")

    if maxes and h0:
        h0.SetMaximum(2.0*max(maxes))
    out += legends(legEntries)
    return out


def fedString(lst=[]):
    return ",".join(["%d" % i for i in lst])


def plotList(f, pad2, offset=None, names=[], logY=True, logX=False, logZ=False, gopts="hist", feds1=[], feds2=[]):
    keep = []

    for iHisto, name in enumerate(names):
        if not name:
            continue
        pad2.cd(offset + iHisto)
        adjustPad(logX=logX, logY=logY, logZ=logZ)
        h = f.Get(name)
        if h:
            shiftFlows(h)
            h.Draw(gopts)
            stylize(h)
            keep.append(h)
            if name == "MatchedTriggerTowers":
                h.SetTitle("(%d #pm %d)" % (h.GetMean(), h.GetRMS()))
            else:
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
                keep += [yx, leg]
        else:
            names = []
            color = [r.kBlack, r.kRed, r.kBlue, r.kGreen, r.kMagenta]
            feds = (feds1 + feds2)[:5]
            color += [r.kBlack] * (len(feds) - len(color))
            style = [1, 2, 3, 4, 5]
            style += [1] * (len(feds) - len(style))
            for iFed, fed in enumerate(sorted(feds)):
                if name == "BcN" and iFed:
                    continue

                names.append((fed, color[iFed], style[iFed]))

            keep += histoLoop(f, names, lambda x: "%s_%d" % (name, x))
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
        h.GetYaxis().SetTitleOffset(0.4)
        r.gPad.SetLogy()
        r.gPad.SetGridy()
    else:
        h = null
        h.Draw()
        labelYAxis(h, labels={1: t[0], 2: t[1], 3: t[2]})
        graph.Draw("psame")

    magnify(h, factor=3.0)
    h.GetXaxis().SetTitleOffset(0.75)
    return graph, h


def onePage(f=None, pad1=None, pad2=None, feds1=[], feds2=[]):
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
                            "nBytesSW", "nWord16Skipped", "ChannelFlavor", "nQieSamples", "ErrF13",
                            "EvN_HTRs", "OrN5_HTRs", "BcN_HTRs",
                            #"TTS", "PopCapFrac",
                            ], feds1=feds1, feds2=feds2)

    # agreement
    keep += plotList(f, pad2, offset=14, names=["adc_vs_adc", "tp_vs_tp"],
                     logY=False, logZ=True, gopts="colz", feds1=feds1, feds2=feds2)

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
    keep += plotList(f, pad2, offset=20, names=["MatchedTriggerTowers"], feds1=feds1, feds2=feds2)

    return keep


def makeSummaryPdf(inputFiles=[], feds1=[], feds2=[], pdf="summary.pdf"):
    r.gROOT.SetStyle("Plain")

    canvas = r.TCanvas()
    canvas.Print(pdf + "[")

    pad1 = r.TPad("pad1", "pad1", 0.00, 0.75, 0.75, 1.00)
    pad2 = r.TPad("pad2", "pad2", 0.00, 0.00, 1.00, 1.00)

    pad2.Divide(5, 4, 0.001, 0.001)
    pad2.Draw()
    pad1.Draw()

    for fileName in inputFiles:
        f = r.TFile(fileName)
        if (not f) or f.IsZombie():
            continue
        junk = onePage(f, pad1, pad2, feds1, feds2)
        canvas.Print(pdf)
        f.Close()
    canvas.Print(pdf + "]")
