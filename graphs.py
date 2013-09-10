import utils
r = utils.ROOT()


def labelAxis(h=None, labels={}):
    h.SetStats(False)
    yaxis = h.GetYaxis()
    for iBin, label in labels.iteritems():
        yaxis.SetBinLabel(iBin, label)
    yaxis.SetLabelSize(2.0*yaxis.GetLabelSize())


def xMax(graph=None, iPoint=None):
    N = graph.GetN()
    iPoint = min(iPoint, N-1) if (iPoint is not None) else N-1
    return graph.GetX()[iPoint]


def magnify(h, factor=1.0):
    for axis in [h.GetXaxis(), h.GetYaxis()]:
        axis.SetLabelSize(factor*axis.GetLabelSize())
        axis.SetTitleSize(factor*axis.GetTitleSize())


def adjustPad(pad=r.gPad, logY=False):
    r.gPad.SetLeftMargin(0.25)
    r.gPad.SetBottomMargin(0.25)
    r.gPad.SetTickx()
    r.gPad.SetTicky()
    if logY:
        r.gPad.SetLogy()


def stylize(h, color=r.kBlack, style=1, width=1):
    #r.gStyle.SetOptStat(110010)
    h.SetStats(False)
    h.SetMinimum(0.5)
    magnify(h, factor=2.0)
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

        gopts = "hist"
        if i:
            gopts += "same"
        else:
            h0 = h
        maxes.append(h.GetMaximum())
        h.Draw(gopts)
        stylize(h, color, style)
        out.append(h)

        legEntries.append((h, h.GetTitle()))
        h.SetTitle("")

    if maxes and h0:
        h0.SetMaximum(2.0*max(maxes))
    out += legends(legEntries)
    return out


def makeSummaryPdf(labels=[], pdf="summary.pdf"):
    canvas = r.TCanvas()
    canvas.Print(pdf+"[")

    pad0 = r.TPad("pad0", "pad0", 0.0, 0.95, 1.0, 1.00)
    pad1 = r.TPad("pad1", "pad1", 0.0, 0.75, 1.0, 0.95)
    pad2 = r.TPad("pad1", "pad1", 0.0, 0.00, 1.0, 0.75)
    pad2.Divide(4, 3)

    pad0.Draw()
    pad1.Draw()
    pad2.Draw()

    for label in labels:
        f = r.TFile("%s/%s.root" % (utils.outputDir(), label))
        if not f:
            continue
        #label
        pad0.cd()
        text = r.TText(0.5, 0.5, label.replace("Run2", "Run 2"))
        text.SetNDC()
        text.SetTextAlign(22)
        text.SetTextSize(20.0*text.GetTextSize())
        text.Draw()

        #category graphs
        graph = f.Get("category_vs_time")
        if not graph:
            continue

        graph.SetMarkerStyle(20)
        graph.SetMarkerColor(r.gStyle.GetHistLineColor())
        graph.SetMarkerSize(0.5*graph.GetMarkerSize())
        t = graph.GetTitle().split("_")

        pad1.cd()
        adjustPad()
        null = r.TH2D("null", ";time (minutes)",
                      1, 0.0, xMax(graph),
                      3, 0.5, 3.5)
        null.Draw()
        magnify(null, factor=3.0)
        labelAxis(null, labels={1: t[0], 2: t[1], 3: t[2]})
        graph.Draw("psame")

        keep = []

        #EvN, OrN, BcN agreement (989 - 714)
        pad2.cd(1)
        adjustPad(logY=True)

        keep += histoLoop(f,
                          [("OrN", r.kBlue, 1),
                           ("EvN", r.kCyan, 2),
                           ("BcN", r.kBlack, 3),
                           ],
                          lambda x: "delta%s" % x,
                          )

        for iHisto, name in enumerate(["", "ErrF0", "PopCapFrac", "TTS",
                                       "", "", "", "",
                                       "", "", "", "",
                                       ]):
            if not name:
                continue
            pad2.cd(1+iHisto)
            adjustPad(logY=True)
            h = f.Get(name)
            if h:
                h.Draw("hist")
                stylize(h)
                keep.append(h)
            else:
                keep += histoLoop(f,
                                  [#(714, r.kRed, 1),
                                   #(722, r.kGreen, 2),
                                   #(989, r.kBlack, 3),
                                   (702, r.kGreen, 2),
                                   (931, r.kBlack, 3),
                                   ],
                                  lambda x: "%s_%d" % (name, x),
                                  )

        canvas.Print(pdf)
        f.Close()
    canvas.Print(pdf+"]")
