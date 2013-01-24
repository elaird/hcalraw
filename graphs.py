import ROOT as r

def labelAxis(h = None, labels = {}) :
    h.SetStats(False)
    yaxis = h.GetYaxis()
    for iBin,label in labels.iteritems() :
        yaxis.SetBinLabel(iBin, label)
    yaxis.SetLabelSize(2.0*yaxis.GetLabelSize())

def makeSummaryPdf(labels = [], pdf = "summary.pdf") :
    canvas = r.TCanvas()
    canvas.Print(pdf+"[")

    pad1 = r.TPad("pad1", "pad1", 0.1, 0.7, 0.9, 0.9)
    pad2 = r.TPad("pad2", "pad2", 0.1, 0.1, 0.5, 0.5)
    pad3 = r.TPad("pad3", "pad3", 0.5, 0.1, 0.9, 0.5)
    pad1.Draw()
    pad2.Draw()
    pad3.Draw()

    for label in labels :
        f = r.TFile("root/%s.root"%label)

        #category graph
        pad1.cd()
        r.gPad.SetLeftMargin(0.25)
        r.gPad.SetTickx()
        r.gPad.SetTicky()

        nBins = 3
        null = r.TH2D("null", "%s;time (minutes)"%label.replace("Run2", "Run 2"),
                      1, 0.0, 4,#1.1*minutes(max(cats.keys())),
                      nBins, 0.5, 0.5+nBins)
        null.Draw()
        gr = f.Get("category_vs_time")
        t = gr.GetTitle().split("_")
        labelAxis(null, labels = {1:t[0], 2:t[1], 3:t[2]})
        gr.SetMarkerStyle(20)
        gr.Draw("psame")

        pad2.cd()
        h2 = f.Get("deltaOrN")
        if h2 :
            h2.SetStats(False)
            h2.Draw("hist")
            h2.SetMinimum(0.5)
            r.gPad.SetLogy()

        pad3.cd()
        h3 = f.Get("deltaBcN")
        if h3 :
            h3.SetStats(False)
            h3.Draw("hist")
            h3.SetMinimum(0.5)
            r.gPad.SetLogy()

        canvas.Print(pdf)
        f.Close()
    canvas.Print(pdf+"]")
