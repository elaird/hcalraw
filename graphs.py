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
    r.gStyle.SetOptStat(110010)
    #h.SetStats(False)
    h.SetMinimum(0.5)
    magnify(h, factor = 2.0)
    h.SetLineWidth(2)

def makeSummaryPdf(labels = [], pdf = "summary.pdf") :
    canvas = r.TCanvas()
    canvas.Print(pdf+"[")

    pad0  = r.TPad("pad0",  "pad0",  0.1, 0.95, 0.9, 1.0)
    pad10 = r.TPad("pad10", "pad10", 0.1, 0.75, 0.9, 0.95)
    pad11 = r.TPad("pad11", "pad11", 0.1, 0.55, 0.9, 0.75)

    pad20 = r.TPad("pad20", "pad20", 0.0, 0.3, 0.3, 0.6)
    #pad21 = r.TPad("pad21", "pad21", 0.3, 0.3, 0.6, 0.6)
    #pad22 = r.TPad("pad22", "pad22", 0.6, 0.3, 0.9, 0.6)

    pad30 = r.TPad("pad30", "pad30", 0.0, 0.0, 0.3, 0.3)
    pad31 = r.TPad("pad31", "pad31", 0.3, 0.0, 0.6, 0.3)
    pad32 = r.TPad("pad32", "pad32", 0.6, 0.0, 0.9, 0.3)

    pad0.Draw()
    pad10.Draw()
    pad11.Draw()

    pad20.Draw()
    #pad21.Draw()
    #pad22.Draw()

    pad30.Draw()
    pad31.Draw()
    pad32.Draw()

    alsoZoom = False

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

        pad10.cd()
        adjustPad()
        null = r.TH2D("null", ";time (minutes)", 1, 0.0, xMax(graph), 3, 0.5, 3.5)
        null.Draw()
        magnify(null, factor = 3.0)
        labelAxis(null, labels = {1:t[0], 2:t[1], 3:t[2]})
        graph.Draw("psame")

        if alsoZoom :
            pad11.cd()
            adjustPad()
            null2 = r.TH2D("null2", ";[first 40 events] time (minutes)", 1, 0.0, xMax(graph, 40), 3, 0.5, 3.5)
            null2.Draw()
            magnify(null2, factor = 3.0)
            labelAxis(null2, labels = {1:t[0], 2:t[1], 3:t[2]})
            graph.Draw("psame")

        keep = []
        pad20.cd()
        adjustPad(logY = True)
        h = f.Get("TTS")
        if h :
            h.Draw("hist")
            stylize(h)
            keep.append(h)

        pad30.cd()
        adjustPad(logY = True)
        h0 = f.Get("deltaOrN")
        if h0 :
            h0.Draw("hist")
            stylize(h0)

        pad31.cd()
        adjustPad(logY = True)
        h1 = f.Get("deltaBcN")
        if h1 :
            h1.Draw("hist")
            stylize(h1)

        pad32.cd()
        adjustPad(logY = True)
        h2 = f.Get("deltaEvN")
        if h2 :
            h2.Draw("hist")
            stylize(h2)

        canvas.Print(pdf)
        f.Close()
    canvas.Print(pdf+"]")
