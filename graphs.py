#!/usr/bin/env python


from options import opts
from configuration import sw
import array
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
    N = graph.GetN()
    X = graph.GetX()
    if not N:
        printer.error("graph contains zero points.")
        return 0.0, 0.0

    x = [X[i] for i in range(N)]
    xMin = min(x)
    xMax = max(x)
    delta = xMax - xMin
    if delta:
        tenPercent = 0.1 * delta
    else:
        tenPercent = 0.1 / 60.0  # 1/10 second
    return (xMin - tenPercent, xMax + tenPercent)


def yCounts(graph=None):
    counts = collections.defaultdict(int)
    y = graph.GetY()
    for i in range(graph.GetN()):
        counts[int(y[i])] += 1
    return counts


def fillRateHisto(h, g):
    n = g.GetN()
    x = g.GetX()
    y = g.GetY()

    # make histo coarser if needed
    if 10 <= n:
        while n < 2 * h.GetNbinsX():
            h.Rebin(2)

    evn = collections.defaultdict(list)
    time = collections.defaultdict(list)
    for i in range(n):
        iBin = h.FindBin(x[i])
        time[iBin].append(x[i])
        evn[iBin].append(y[i])


    for iBin in evn.keys():
        times = time[iBin]
        evns = evn[iBin]
        nL1A = 1 + max(evns) - min(evns)
        if len(evns) == 1:
            deltaT = h.GetBinWidth(iBin)
        else:
            deltaT = max(times) - min(times)
            deltaT *= 1.0 + 1.0 / len(times)  # "wait" one event
        deltaT *= 60.0  # minutes --> seconds

        c = nL1A / deltaT
        h.SetBinContent(iBin, c)

        relErr = 1.0 / len(evns)  # +- 1 events
        h.SetBinError(iBin, c * relErr)


def magnify(h, factor=1.0):
    h.GetYaxis().SetTitleOffset(1.2)
    h.GetZaxis().SetTitleOffset(1.2)

    default = 0.035
    for axis in [h.GetXaxis(), h.GetYaxis(), h.GetZaxis()][:2]:
        axis.SetLabelSize(factor * default)
        axis.SetTitleSize(factor * default)



def adjustPad(pad=r.gPad, logX=False, logY=False, logZ=False, gridX=False, gridY=False,
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
    if gridX:
        r.gPad.SetGridx()
    if gridY:
        r.gPad.SetGridy()


def stylize(h, color=r.kBlack, style=1, width=1):
    h.SetStats(False)
    h.SetMinimum(0.5)
    h.SetLineColor(color)
    h.SetLineStyle(style)
    h.SetLineWidth(width)


def legends(legEntries=[], twoLines=False, gopts="l"):
    out = []
    dx = 0.8 / max(1, len(legEntries))
    dx *= 2 if twoLines else 1
    if twoLines:
        max1 = len(legEntries)/2
        y = 0.95
    else:
        max1 = len(legEntries)
        y = 0.91

    x0 = 0.1
    for iLeg in range(max1):
        h, desc = legEntries[iLeg]
        leg = r.TLegend(x0, y, x0+dx, 1.0)
        x0 += dx
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.AddEntry(h, desc, gopts)
        leg.Draw()
        out.append(leg)

    x0 = 0.1
    for iLeg in range(max1, len(legEntries)):
        h, desc = legEntries[iLeg]
        leg2 = r.TLegend(x0, 0.90, x0+dx, y)
        x0 += dx
        leg2.SetBorderSize(0)
        leg2.SetFillStyle(0)
        leg2.AddEntry(h, desc, gopts)
        leg2.Draw()
        out.append(leg2)

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
    twoLines = False
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
        if not h.GetXaxis().GetTitle():
            h.GetXaxis().SetLabelSize(0.13)
        if h.GetXaxis().GetTitle() == "channel flavor":
            h.GetXaxis().SetLabelSize(0.10)
        out.append(h)

        s = "Matched"
        if func(x).startswith(s):
            twoLines = True
            ch = func(x).replace(s, "").replace("Fibers", "").replace("TriggerTowers", "")
            if not ch:
                ch = "TP  "
            t = "%s  %d#pm%d" % (ch, h.GetMean(), h.GetRMS())
        else:
            t = h.GetTitle().replace("FED ", "")

        if justOne(func(x)):
            t += "   (%d entries)" % h.GetEntries()

        legEntries.append((h, t))
        h.SetTitle("")

    if maxes and h0:
        h0.SetMaximum(2.0*max(maxes))
    out += legends(legEntries, twoLines=twoLines)
    return out


def graphLoop(f, lst, func):
    out = []
    legEntries = []
    h0 = None

    didOne = False
    twoLines = False

    mins = []
    maxs = []
    for x, _, _ in lst:
        g = f.Get(func(x))
        if not g:
            continue
        xMin, xMax = xMin_xMax(g)
        mins.append(xMin)
        maxs.append(xMax)

    for x, color, style in lst:
        g = f.Get(func(x))
        if not g:
            continue

        if not g.GetN():
            continue

        title, xTitle, yTitle = g.GetTitle().split(";")
        if not h0:
            h0 = r.TH2D("h0_%s" % g.GetName(), ";%s;%s" % (xTitle, yTitle), 1, min(mins), max(maxs), 1, -0.1, 1.1)
            h0.SetStats(False)
            magnify(h0, factor=1.8)
            h0.GetYaxis().SetTitleOffset(0.6)
            h0.Draw()
            out.append(h0)

        g.Draw("psame")
        g.SetMarkerColor(color)
        g.SetMarkerStyle(20)
        g.SetMarkerSize(0.3)
        out.append(g)

        legEntries.append((g, title.replace("FED ", "")))

    out += legends(legEntries, gopts="p")
    return out


def fedString(lst=[]):
    return ",".join(["%d" % i for i in lst])


def drawCrates():
    b = r.TBox()
    b.SetFillStyle(0)
    b.SetLineColor(r.kBlack)
    b.SetLineStyle(3)
    y = 4.5
    return [b.DrawBox( 0.5, 0.5, 12.5,   y),  # uTCA
            b.DrawBox( 1.5,   y,  7.5, 6.5),
            b.DrawBox( 7.5,   y,  8.5, 6.5),
            b.DrawBox(12.5,   y, 18.5, 6.5),
            b.DrawBox(20.5,   y, 21.5, 6.5),
            ]


def summed(f=None, names=[]):
    out = None
    for name in names:
        h = f.Get(name)
        if not h:
            continue
        if out is None:
            out = h.Clone()
        else:
            out.Add(h)
    return out


def frac0_all_good(h=None):
    h.RebinX(36)
    for iBinX in range(1, 1 + h.GetNbinsX()):
        hy = h.ProjectionY("py_%d" % iBinX, iBinX, iBinX)
        bin1 = hy.FindBin(1.0)
        if hy.Integral(1, bin1 - 1):
            return False
    return True


def all_diagonal(h=None):
    for iBinX in range(1, 1 + h.GetNbinsX()):
        for iBinY in range(1, 1 + h.GetNbinsY()):
            if iBinX == iBinY:  # skip diagonal
                continue
            if h.GetBinContent(iBinX, iBinY):
                return False
    return True


def full_utca_crate(h):
    return full_crate(h, slots=range(1, 13), fibers=(range(2, 10) + range(14, 22)))


def full_crate(h=None, slots=[], fibers=[]):
    # FIXME: since histogram is already summed over FEDs,
    # this function would fail to plot in the very unlikely
    # situation that different FEDs' problems compensate each others' counts

    s = set()
    for slot in slots:
        iBinX = h.GetXaxis().FindBin(slot)
        for fiber in fibers:
            iBinY = h.GetYaxis().FindBin(fiber)
            s.add(h.GetBinContent(iBinX, iBinY))
    return len(s) == 1


def divided(numer, denom, zero=-1.0e-3):
    for iBinX in range(2 + numer.GetNbinsX()):
        for iBinY in range(2 + numer.GetNbinsY()):
            a = numer.GetBinContent(iBinX, iBinY)
            b = denom.GetBinContent(iBinX, iBinY)
            if a == 0.0 and b != 0.0:
                content = zero  # yikes!
            elif b == 0.0:
                content = -1.0  # below color range: white
            else:
                content = a / b

            numer.SetBinContent(iBinX, iBinY, content)
    return numer


def plotGlobal(f, pad, offset=None, names=[], logY=False, logX=False, logZ=True,
               gopts="colz", feds1=[], feds2=[], doYx=True, retitle=True,
               gridX=False, gridY=False, boxes=False, denoms={}):
    keep = []
    if denoms:
        logZ = False

    for iHisto, name in enumerate(names):
        if not name:
            continue
        pad.cd(offset + iHisto)
        adjustPad(logX=logX, logY=logY, logZ=logZ,
                  gridX=gridX, gridY=gridY)
        h = f.Get(name)
        if not h:
            continue

        shiftFlows(h)
        zTitle = "Samples / bin"
        if denoms.get(name):
            denom = f.Get(denoms[name])
            if not denom:
                printer.error("%s not found" % denoms[name])
                continue
            shiftFlows(denom)
            h = divided(h, denom)
            zTitle = "# (%s)  /  # (%s)" % (h.GetTitle(), denom.GetTitle())
            h.GetZaxis().SetTitle(zTitle)
        else:
            denom = None

        h.Draw(gopts)
        stylize(h)
        magnify(h, factor=1.8)
        if denom:
            iGray = 56
            colors = [19] * (iGray - 51) + range(iGray, 51 + 50)
            r.gStyle.SetPalette(len(colors), array.array('i', colors))

            h.GetZaxis().SetRangeUser(-0.1, 1.1)
            nContours = 12
            r.gStyle.SetNumberContours(nContours)  # restored in pageTwo()
            h.SetContour(nContours)
        else:
            h.GetZaxis().SetRangeUser(0.5, h.GetMaximum())

        if boxes:
            keep += drawCrates()

        if retitle:
            P = name[:name.find("_vs_")].upper()
            h.GetXaxis().SetTitle("%s" % fedString(feds1))
            h.GetYaxis().SetTitle("%s" % fedString(feds2))
            h.GetZaxis().SetTitle(zTitle)

            title = P
            if h.GetTitle():
                note = h.GetTitle().replace("SOI; ", "")
                if note:
                    h.GetXaxis().SetTitle("%s  (%s)" % (h.GetXaxis().GetTitle(), note))
                if h.GetTitle().startswith("SOI"):
                    title += " (SOI)"
            h.SetTitle(title)

        xMin = h.GetXaxis().GetXmin()
        xMax = h.GetXaxis().GetXmax()

        line = r.TLine()
        line.SetLineWidth(1)
        line.SetLineStyle(2)
        # if doYx:
        #     x0 = line.DrawLine(0.0, xMin, 0.0, xMax)
        #     y0 = line.DrawLine(xMin, 0.0, xMax, 0.0)
        #     keep += [x0, y0]

        h.Draw(gopts + "same")  # draw again to be on top of dashed lines

        yx = r.TF1("yx", "x", -0.5, xMax)
        yx.SetNpx(int(0.5 + xMax))
        yx.SetLineColor(r.kBlack)
        yx.SetLineWidth(1)
        yx.SetLineStyle(3)
        if doYx:
            yx.Draw("same")

        leg = r.TLegend(0.25, 0.73, 0.4, 0.85)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)

        if doYx:
            leg.AddEntry(yx, "y = x", "l")
            # leg.AddEntry(x0, "zero", "l")

        leg.Draw()
        keep += [h, yx, leg]
        # if name == "adc_vs_adc":
        #     h.SetTitle("")
        #     h.GetXaxis().SetTitle("ADC  (VME FEDs 718,719)")
        #     h.GetYaxis().SetTitle("ADC  (uTCA FED 1118)")
        #     r.gPad.Print("adc.pdf")
        #     import os
        #     os.system("pdfcrop adc.pdf")

    return keep


def plotList(f, pad, offset=None, names=[],
             logY=True, logX=False, logZ=False,
             gridX=False, gridY=False,
             feds1=[], feds2=[],
             func=histoLoop):

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
        adjustPad(logX=logX, logY=logY, logZ=logZ,
                  gridX=gridX, gridY=gridY)

        feds = []
        for iFed, fed in enumerate(sorted(fedList)):
            feds.append((fed, color[iFed], style[iFed]))

        keep += func(f, feds, lambda x: "%s_%d" % (name, x))
    return keep


def resyncs(graph=None, maximum=None):
    n = graph.GetN()
    x = graph.GetX()
    y = graph.GetY()

    i2 = 0
    gr2 = r.TGraph()
    for i in range(n):
        if not y[i]:
            gr2.SetPoint(i2, x[i], maximum)
            i2 += 1
    return gr2


def big_clean(size=None, frac0=None, sizeMin=None, frac0Min=None, height=None):
    if (not size) or (not frac0):
        return

    n = size.GetN()
    sX = size.GetX()
    sY = size.GetY()

    fX = frac0.GetX()
    fY = frac0.GetY()

    i2 = 0
    gr2 = r.TGraph()
    for i in range(n):
        if sizeMin < sY[i] and frac0Min < fY[i]:
            gr2.SetPoint(i2, sX[i], height)
            i2 += 1
    return gr2


def anyVisible(graph=None, maximum=None):
    n = graph.GetN()
    y = graph.GetY()
    for i in range(n):
        if y[i] <= maximum:
            return True
    return False


def stamp(title, size=0.045, x=0.01, y=0.99):
    latex = r.TLatex()
    latex.SetNDC()
    latex.SetTextAngle(90)
    latex.SetTextSize(size)
    latex.SetTextAlign(33)
    return latex.DrawLatex(x, y, "#color[46]{%s}" % title)


def draw_graph(graph=None, title="", ratemax=None, graph2=None, graph3=None, graph4=None):
    if not graph or not graph.GetN():
        return

    padg = r.TPad("padg", "padg", 0.00, 0.75, 0.80, 1.00)
    padg.Draw()
    keep = [padg]

    if ratemax:
        split = 0.3
        padg.Divide(1, 2)
        padg.cd(1).SetPad(0.01, split, 0.99, 0.99 )
        padg.cd(2).SetPad(0.01, 0.01 , 0.99, split)

    graph.SetMarkerStyle(20)
    graph.SetMarkerColor(r.gStyle.GetHistLineColor())
    graph.SetMarkerSize(0.5*graph.GetMarkerSize())

    xMin, xMax = xMin_xMax(graph)
    bargs = (xMin, xMax, 3, 0.5, 3.5)

    # nBins power of two for repeated rebin(2)
    null_title = ";"
    if "/store" in graph.GetTitle():
        null_title += "%s%s" % (graph.GetTitle(), " " * 10)

    null_title += "time (minutes);"
    null_coarse = r.TH2D("null_coarse", null_title,   4, *bargs)
    null_fine   = r.TH2D("null_fine",   null_title, 128, *bargs)

    rateColorFine = r.kGray
    rateColorCoarse = 602
    bxColor = r.kRed
    resyncColor = r.kGreen
    splashColor = r.kMagenta

    if ratemax:
        h = null_coarse.ProjectionX()
        g = null_fine.ProjectionX()
        fillRateHisto(h, graph)
        fillRateHisto(g, graph)
        for histo in [h, g]:
            histo.SetStats(False)
            histo.SetMarkerStyle(20)
            histo.SetMarkerSize(0.5)

        h.SetMarkerColor(rateColorCoarse)
        h.SetLineColor(rateColorCoarse)
        g.SetMarkerColor(rateColorFine)
        g.SetLineColor(rateColorFine)

        y = 10.0

        padg.cd(1)
        adjustPad(m={"Bottom": 0.0, "Left": 0.1, "Top": 0.03, "Right": 0.03})
        r.gPad.SetLogy(True)
        r.gPad.SetGridy()
        hu = g.DrawClone("pe")
        hu2 = h.DrawClone("pesame")
        RColor = resyncColor if (graph3 and graph3.GetN()) else 0
        SColor = splashColor if (graph4 and graph4.GetN()) else 0

        yTitle = "#splitline{#color[%d]{coarse}  #color[%d]{fine}}{L1A rate (Hz)}" % (rateColorCoarse, rateColorFine)
        yTitle += " #splitline{#color[%d]{R}}{#color[%d]{S}}" % (RColor, SColor)

        hu.GetYaxis().SetTitle(yTitle)
        hu.GetXaxis().SetLabelSize(0.0)
        hu.GetXaxis().SetNoExponent(True)
        hu.GetXaxis().SetTickLength(0.0)
        hu.SetMinimum(y)
        hu.SetMaximum(ratemax)
        keep += [hu, hu2]
        magnify(hu, factor=3.0)
        hu.GetYaxis().SetTitleSize(0.13)
        hu.GetYaxis().SetTitleOffset(0.25)
        hu.GetYaxis().SetLabelOffset(0.001)

        if graph2:
            anyVisible2 = anyVisible(graph2, hu.GetMaximum())
            if anyVisible2:
                graph2.SetMarkerColor(bxColor)
                graph2.SetMarkerSize(0.3)
                graph2.Draw("psame")
                keep.append(graph2)

        if graph3 and graph3.GetN():
            graph3.SetMarkerStyle(20)
            graph3.SetMarkerColor(resyncColor)
            graph3.SetMarkerSize(0.5)
            graph3.Draw("psame")
            keep.append(graph3)

        if graph4 and graph4.GetN():
            graph4.SetMarkerStyle(29)
            graph4.SetMarkerColor(splashColor)
            graph4.SetMarkerSize(0.5)
            graph4.Draw("psame")
            keep.append(graph4)

        padg.cd(2)
        adjustPad(m={"Bottom": 0.5, "Left": 0.1, "Top": 0.0, "Right": 0.03})
        r.gPad.SetLogy(False)
        r.gPad.SetTickx(0)
        hl = g.DrawClone("pe")
        hl2 = h.DrawClone("pesame")
        hl.SetMinimum(0.0)
        hl.SetMaximum(y)
        keep += [hl, hl2]
        magnify(hl, factor=9.0)
        hl.GetXaxis().SetTickLength(0.1)
        hl.GetXaxis().SetTitleOffset(0.85)
        hl.GetXaxis().SetTitleSize(0.25)
        hl.GetXaxis().SetNoExponent(True)
        hl.GetYaxis().SetTickLength(hu.GetYaxis().GetTickLength())
        hl.GetYaxis().SetLabelSize(0.25)
        hl.GetYaxis().SetNdivisions(402, True)

        if graph2 and anyVisible2:
            graph2.Draw("psame")
            hl.GetYaxis().SetTitle("#DeltaBX")
            hl.GetYaxis().SetTitleColor(bxColor)
            hl.GetYaxis().SetTitleOffset(0.09)
            r.gPad.SetGridy()

    else:
        padg.Draw()
        padg.cd()

        adjustPad(m={"Bottom": 0.2, "Left": 0.15, "Top": 0.03, "Right": 0.03})
        null_coarse.Draw()
        magnify(null_coarse, factor=3.0)
        t = graph.GetTitle().split("_")
        labelYAxis(null_coarse, labels={1: t[0], 2: t[1], 3: t[2]})
        graph.Draw("psame")
        keep += [null_coarse, graph]
        null_coarse.GetXaxis().SetTitleOffset(0.75)
        null_coarse.GetYaxis().SetLabelSize(0.1)

    padg.cd(0)
    keep.append(stamp(title, size=0.17, x=0.01, y=0.98))

    # padg.Print("output/%s_l1a.pdf" % title.replace("Run ", ""))
    return keep


def relabel(cats, counts):
    labels = []
    for i, label in enumerate(cats.GetTitle().split("_")):
        labels.append("%s (%d)" % (label, counts[1 + i]))
    cats.SetTitle("_".join(labels))


def retitle(evn_graph):
    fields = evn_graph.GetTitle().split(",")[0].split("/")
    title = "/".join(fields[:-2])
    title = title[title.find("/store"):]
    evn_graph.SetTitle(title)


def fedSum(f=None, prefix="", feds=[]):
    h = None
    for fed in feds:
        h1 = f.Get("%s_%d" % (prefix, fed))
        if not h1:
            continue
        if h:
            h.Add(h1)
        else:
            h = h1.Clone()
    return h


def plotZS(f, pad0, feds2):
    pad0.cd(3)
    adjustPad(logY=True)

    ha1 = fedSum(f, "channel_peak_adc_mp1", feds2)
    ha0 = fedSum(f, "channel_peak_adc_mp0", feds2)
    maxes = []
    for h in [ha1, ha0]:
        if not h:
            continue
        h.SetTitle(fedString(feds2))
        shiftFlows(h)
        stylize(h, r.kBlue, 1)
        magnify(h, factor=1.8)
        maxes.append(h.GetMaximum())

    if maxes:
        hMax = 2.0 * max(maxes)
    else:
        hMax = None

    leg = r.TLegend(0.17, 0.80, 0.32, 0.92)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)

    same = ""
    if ha1:
        color1 = r.kCyan
        stylize(ha1, color1, 2)
        ha1.Draw("hist")
        ha1.SetMaximum(hMax)
        leg.AddEntry(ha1, "M&P", "l")
        same = "same"
    if ha0:
        stylize(ha0, r.kBlue, 1)
        ha0.Draw("hist%s" % same)
        ha0.SetMaximum(hMax)
    leg.Draw()

    pad0.cd(6)
    adjustPad(logY=True)

    ht1 = f.Get("tp_vs_tp_soi2_mp0")
    # ht1 = fedSum(f, "channel_peak_tp", feds2)
    if ht1:
        ht1.SetTitle("%s;TP E_{SOI};Trigger Towers / bin" % fedString(feds2))
        # ht1.SetTitle("%s;Peak TP E;Trigger Towers / bin" % fedString(feds2))
        shiftFlows(ht1)
        ht1.Draw("hist")
        ht1.GetXaxis().SetRangeUser(-0.5, 13.5)
        stylize(ht1, r.kBlue, 1)
        magnify(ht1, factor=1.8)

    return [ha0, ha1, leg, ht1]


def suffix(feds1, feds2):
    out = "_%d" % feds1[0]
    if feds2:
        out += "_%d" % feds2[0]
    return out


def pageOne(f=None, feds1=[], feds2=[], canvas=None, pdf="", title=""):
    pad20 = r.TPad("pad20", "pad20", 0.00, 0.00, 1.00, 1.00)
    pad20.Divide(5, 4, 0.001, 0.001)
    pad20.Draw()

    keep = []

    sfx = suffix(feds1, feds2)

    cats = f.Get("category_vs_time" + sfx)
    if not cats:
        return
    if not cats.GetN():
        return

    counts = yCounts(cats)
    if 2 <= len(counts.keys()):
        relabel(cats, counts)
        keep += draw_graph(cats, title=title)
    else:
        ratemax = 5.0e7

        evn_graph = f.Get("evn_vs_time" + sfx)
        retitle(evn_graph)

        if "/239/895" in evn_graph.GetTitle():
            graph4 = big_clean(size=f.Get("kB_vs_time_%d" % feds1[0]),
                               frac0=f.Get("frac0_vs_time_%d" % feds1[0]),
                               sizeMin=0.8,
                               frac0Min=0.2,
                               height=ratemax / 5.0)
        else:
            graph4 = None

        keep += draw_graph(graph=evn_graph,
                           title=title, ratemax=ratemax,
                           graph2=f.Get("bcn_delta_vs_time" + sfx),
                           graph3=resyncs(f.Get("incr_evn_vs_time" + sfx), ratemax),
                           graph4=graph4,
                           )

    # single FED
    keep += plotList(f, pad20, offset=5,
                     names=["BcN",
                            "nBytesSW", "ChannelFlavor", "nQieSamples", "nTpSamples", "htrOverviewBits",
                            "EvN_HTRs", "OrN5_HTRs", "BcN_HTRs", "ErrF0",
                            # "TTS", "PopCapFrac",
                            ], feds1=feds1, feds2=feds2)

    # EvN, OrN, BcN agreement
    if not feds1:
        printer.error(" in graphs.py pageOne: feds1 = %s" % str(feds1))
        return

    fed1 = sorted(feds1)[0]
    for i, fed2 in enumerate(feds2[:3]):
        pad20.cd(16 + i)
        adjustPad(logY=True)
        keep += histoLoop(f,
                          [("EvN", r.kBlue, 1),
                           ("OrN", r.kCyan, 2),
                           ("BcN", r.kBlack, 3),
                           ],
                          lambda x: "delta%s_%s_%s" % (x, fed1, fed2),
                          )

    # TS
    pad20.cd(15)
    adjustPad(logY=True)
    keep += histoLoop(f,
                      [("nTS_for_matching_ADC", r.kBlue, 1),
                       ("nTS_for_matching_TP", r.kCyan, 2),
                       ],
                      lambda x: x,
                      )

    # fibers
    pad20.cd(19)
    adjustPad(logY=True)
    keep += histoLoop(f,
                      [("MatchedFibersCh0", r.kBlue, 1),
                       ("MatchedFibersCh1", r.kCyan, 2),
                       ("MatchedFibersCh2", r.kBlack, 3),
                       ("MatchedTriggerTowers", r.kGreen, 4),
                       ],
                      lambda x: x,
                      )

    pad20.cd(20)
    adjustPad(logY=True)
    keep += histoLoop(f,
                      [("MisMatchedFibersCh0", r.kBlue, 1),
                       ("MisMatchedFibersCh1", r.kCyan, 2),
                       ("MisMatchedFibersCh2", r.kBlack, 3),
                       ("MisMatchedTriggerTowers", r.kGreen, 4),
                       ],
                      lambda x: x,
                      )

    canvas.Print(pdf)


def pageTwo(f=None, feds1=[], feds2=[], canvas=None, pdf="", names=[], title="", denoms={},
            doYx=True, retitle=True, gridX=False, gridY=False, boxes=False, alsoZs=False):

    # don't print blank page
    if not any([f.Get(name) for name in names]):
        return

    pad0 = r.TPad("pad0", "pad0", 0.00, 0.00, 1.00, 1.00)
    if len(names) <= 3:
        pad0.Divide(len(names), 1)
    else:
        pad0.DivideSquare(len(names))

    pad0.Draw()

    kargs = {}
    for item in ["feds1", "feds2", "names", "denoms", "doYx", "retitle", "gridX", "gridY", "boxes"]:
        kargs[item] = eval(item)

    nContours = r.gStyle.GetNumberContours()
    keep = plotGlobal(f, pad0, offset=1, **kargs)
    if alsoZs:
        keep += plotZS(f, pad0, feds2)

    if title:
        pad0.cd(0)
        keep.append(stamp(title))

    canvas.Print(pdf)
    r.gStyle.SetPalette(1)
    r.gStyle.SetNumberContours(nContours)


def pageThree(stem, suppress=lambda x: False, yx=False, keys=["feds1", "feds2"], **kargs):
    names = []
    for key in keys:
        names += [stem % x for x in kargs[key][:3]]
    names += [""] * 6
    names = names[:6]
    h = summed(kargs["f"], names)

    if not suppress(h):
        pageTwo(names=names, doYx=yx, retitle=False, gridX=True, **kargs)


def pageTrends(f=None, feds1=[], feds2=[], canvas=None, pdf="", title="", names=[]):
    pad0 = r.TPad("pad0", "pad0", 0.00, 0.00, 1.00, 1.00)
    pad0.Divide(1, len(names))
    pad0.Draw()

    keep = []
    for iName, name in enumerate(names):
        keep += plotList(f, pad0, offset=1 + iName, names=[name],
                         logY=False, logX=False, logZ=False, gridY=True,
                         feds1=feds1, feds2=feds2, func=graphLoop)

    if title:
        pad0.cd(0)
        keep.append(stamp(title))
    canvas.Print(pdf)


def makeSummaryPdfMulti(inputFiles=[], feds1s=[], feds2s=[], pdf="summary.pdf", pages=range(1, 100)):
    r.gROOT.SetBatch(True)
    r.gErrorIgnoreLevel = r.kWarning

    r.gStyle.SetTitleBorderSize(0)
    r.gStyle.SetTitleX(0.53)
    r.gStyle.SetTitleY(0.95)
    r.gStyle.SetTitleFontSize(0.07)
    r.gStyle.SetTitleAlign(22)
    r.gStyle.SetGridStyle(2)

    canvas = r.TCanvas()
    canvas.Print(pdf + "[")

    for fileName, feds1, feds2 in zip(inputFiles, feds1s, feds2s):
        f = r.TFile(fileName)
        if (not f) or f.IsZombie():
            continue

        title = f.GetPath().replace("output/", "").replace(".root:/", "")
        if "_" not in title:
            title = "Run %s" % title

        kargs = {}
        for item in ["f", "feds1", "feds2", "canvas", "pdf", "title"]:
            kargs[item] = eval(item)

        if 1 in pages:
            pageOne(**kargs)
            kargs["title"] = ""  # don't stamp later pages

        if feds2 and 2 in pages:
            pageTwo(names=["adc_vs_adc", "adc_vs_adc_soi_both", "",
                           "tp_vs_tp", "tp_vs_tp_soi_both", ""],
                    alsoZs=True, **kargs)

        names = ["%s_mismatch_vs_slot_crate" % k for k in ["EvN", "OrN5", "BcN"]]
        names += ["ErrFNZ_vs_slot_crate", "ADC_mismatch_vs_slot_crate", "TP_mismatch_vs_slot_crate"]

        kargs34 = {"names": names, "doYx": False, "retitle": False, "boxes": True}
        kargs34.update(kargs)

        if 3 in pages:
            pageTwo(**kargs34)

        if 4 in pages:
            denoms = {"EvN_mismatch_vs_slot_crate": "block_vs_slot_crate",
                      "OrN5_mismatch_vs_slot_crate": "block_vs_slot_crate",
                      "BcN_mismatch_vs_slot_crate": "block_vs_slot_crate",
                      "ErrFNZ_vs_slot_crate": "ErrFAny_vs_slot_crate",
                      "ADC_mismatch_vs_slot_crate": "ErrF0_vs_slot_crate",
                      "TP_mismatch_vs_slot_crate": "TP_matchable_vs_slot_crate",
                      }
            pageTwo(denoms=denoms, **kargs34)

        if 5 in pages:
            pageThree(stem="frac0_vs_BcN_%d", suppress=frac0_all_good, **kargs)

        if 6 in pages:
            pageThree(stem="EvN_HTR_vs_FED_%d", suppress=all_diagonal, yx=True, **kargs)

        if 7 in pages:
            pageThree(stem="OrN5_HTR_vs_FED_%d", suppress=all_diagonal, yx=True, **kargs)

        if 8 in pages:
            pageTrends(names=["fracEvN_vs_time", "frac0_vs_time", "ADC_misMatch_vs_time"], **kargs)

        if 9 in pages:
            pageThree(stem="fiber_vs_slot_%d", suppress=full_utca_crate, keys=["feds2"], **kargs)

        f.Close()
    canvas.Print(pdf + "]")


def makeSummaryPdf(inputFile="", feds1=[], feds2=[], pdf="summary.pdf"):
    makeSummaryPdfMulti(inputFiles=[inputFile], feds1s=[feds1], feds2s=[feds2], pdf=pdf)


def main(options):
    makeSummaryPdf(inputFile=options.outputFile,
                   feds1=sw.fedList(options.feds1),
                   feds2=sw.fedList(options.feds2),
                   pdf=options.outputFile.replace(".root", ".pdf"),
    )


if __name__ == "__main__":
    main(opts()[0])
