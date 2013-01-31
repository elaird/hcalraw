import ROOT as r

def labelAxis(h = None, labels = {}) :
    h.SetStats(False)
    yaxis = h.GetYaxis()
    for iBin,label in labels.iteritems() :
        yaxis.SetBinLabel(iBin, label)
    yaxis.SetLabelSize(2.0*yaxis.GetLabelSize())

def xMax(graph = None, iPoint = None) :
    N = graph.GetN()
    iPoint = min(iPoint, N-1) if iPoint!=None else N-1
    x = r.Double()
    y = r.Double()
    graph.GetPoint(iPoint, x, y)
    return float(x)

def magnify(h, factor = 1.0) :
    for axis in [h.GetXaxis(), h.GetYaxis()] :
        axis.SetLabelSize(factor*axis.GetLabelSize())
        axis.SetTitleSize(factor*axis.GetTitleSize())

def adjustPad(pad = r.gPad, logY = False) :
    r.gPad.SetLeftMargin(0.25)
    r.gPad.SetBottomMargin(0.25)
    r.gPad.SetTickx()
    r.gPad.SetTicky()
    if logY : r.gPad.SetLogy()

def stylize(h) :
    #r.gStyle.SetOptStat(110010)
    h.SetStats(False)
    h.SetMinimum(0.5)
    magnify(h, factor = 2.0)
    h.SetLineWidth(2)

def makeSummaryPdf(labels = [], pdf = "summary.pdf") :
    canvas = r.TCanvas()
    canvas.Print(pdf+"[")

    pad0  = r.TPad("pad0",  "pad0",  0.0, 0.95, 1.0, 1.00)
    pad1  = r.TPad("pad1",  "pad1",  0.0, 0.75, 1.0, 0.95)
    pad2  = r.TPad("pad1",  "pad1",  0.0, 0.00, 1.0, 0.75)
    pad2.Divide(3,3)

    pad0.Draw()
    pad1.Draw()
    pad2.Draw()

    for label in labels :
        f = r.TFile("root/%s.root"%label)

        #label
        pad0.cd()
        text = r.TText(0.5, 0.5, label.replace("Run2", "Run 2"))
        text.SetNDC()
        text.SetTextAlign(22)
        text.SetTextSize(20.0*text.GetTextSize())
        text.Draw()

        #category graphs
        graph = f.Get("category_vs_time")
        graph.SetMarkerStyle(20)
        graph.SetMarkerColor(r.gStyle.GetHistLineColor())
        graph.SetMarkerSize(0.5*graph.GetMarkerSize())
        t = graph.GetTitle().split("_")

        pad1.cd()
        adjustPad()
        null = r.TH2D("null", ";time (minutes)", 1, 0.0, xMax(graph), 3, 0.5, 3.5)
        null.Draw()
        magnify(null, factor = 3.0)
        labelAxis(null, labels = {1:t[0], 2:t[1], 3:t[2]})
        graph.Draw("psame")

        keep = []
        for iHisto,name in enumerate(["deltaOrN", "deltaBcN", "deltaEvN",
                                      "ErrF0_989","PopCapFrac_989", "TTS_989",
                                      "ErrF0_714","PopCapFrac_714", "TTS_714",
                                      ]) :
            pad2.cd(1+iHisto)
            adjustPad(logY = True)
            h = f.Get(name)
            if h :
                h.Draw("hist")
                stylize(h)
                keep.append(h)

        canvas.Print(pdf)
        f.Close()
    canvas.Print(pdf+"]")
