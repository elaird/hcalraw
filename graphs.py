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

    canvas.SetLeftMargin(0.25)
    canvas.SetTickx()
    canvas.SetTicky()

    for label in labels :
        f = r.TFile("root/%s.root"%label)

        #category graph
        nBins = 30
        null = r.TH2D("null", "%s;time (minutes)"%label.replace("Run2", "Run 2"),
                      1, 0.0, 4,#1.1*minutes(max(cats.keys())),
                      nBins, 0.5, 0.5+nBins)
        null.Draw()
        gr = f.Get("category_vs_time")
        t = gr.GetTitle().split("_")
        labelAxis(null, labels = {1:t[0], 2:t[1], 3:t[2]})
        gr.SetMarkerStyle(20)
        gr.Draw("psame")

        canvas.Print(pdf)
        f.Close()
    canvas.Print(pdf+"]")
