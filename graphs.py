import ROOT as r

def minutes(orn) :
    orbPerSec = 11.1e3
    return orn/orbPerSec/60.0

def categories(oMap = {}, iMap = {}, innerEvent = {}) :
    d = {}
    for oEvent,ornEvn in oMap.iteritems() :
        orn = ornEvn[0]
        if oEvent in innerEvent and innerEvent[oEvent]!=None :
            d[orn] = 3
        else :
            d[orn] = 2

    iEvents = innerEvent.values()
    for iEvent,ornEvn in iMap.iteritems() :
        if iEvent in iEvents : continue
        orn = ornEvn[0]
        d[orn] = 1

    return d

def graph(d = {}) :
    gr = r.TGraph()
    for i,key in enumerate(sorted(d.keys())) :
        gr.SetPoint(i, minutes(key), d[key])
    return gr

def labelAxis(h = None, labels = {}) :
    h.SetStats(False)
    yaxis = h.GetYaxis()
    for iBin,label in labels.iteritems() :
        yaxis.SetBinLabel(iBin, label)
    yaxis.SetLabelSize(2.0*yaxis.GetLabelSize())

def writePdf(label = "", oLabel = "", iLabel = "",
             oMapF = {}, iMapF = {}, innerEvent = {}) :
    cats = categories(oMap = oMapF, iMap = iMapF, innerEvent = innerEvent)
    gr = graph(cats)
    nBins = 30
    null = r.TH2D("null", "%s;time (minutes)"%label.replace("Run2", "Run 2"),
                  1, 0.0, 4,#1.1*minutes(max(cats.keys())),
                  nBins, 0.5, 0.5+nBins)

    canvas = r.TCanvas()
    canvas.SetLeftMargin(0.25)
    canvas.SetTickx()
    canvas.SetTicky()

    null.Draw()
    nBoth = len(filter(lambda x:x!=None,innerEvent.values()))
    labelAxis(null, labels = {1:"only %s (%d)"%(iLabel, len(iMapF)-nBoth),
                              2:"only %s (%d)"%(oLabel, len(oMapF)-nBoth),
                              3:"both (%d)"%nBoth})

    gr.SetMarkerStyle(20)
    gr.Draw("psame")
    canvas.Print("%s.pdf"%label)
