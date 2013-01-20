import ROOT as r

def minutes(orn, bcn, evn = None) :
    orbPerSec = 11.1e3
    sec = (orn+bcn/3564.)/orbPerSec
    return sec/60.0

def categories(outer = [], inner = []) :
    d = {}
    for ornBcn in set(outer + inner) :
        cat = 0
        if ornBcn in inner : cat += 1
        if ornBcn in outer : cat += 2
        d[ornBcn] = cat
    return d

def graph(d = {}) :
    gr = r.TGraph()
    for i,key in enumerate(sorted(d.keys())) :
        gr.SetPoint(i, minutes(*key), d[key])
    return gr

def labelAxis(h = None, labels = {}) :
    h.SetStats(False)
    yaxis = h.GetYaxis()
    for iBin,label in labels.iteritems() :
        yaxis.SetBinLabel(iBin, label)
    yaxis.SetLabelSize(2.0*yaxis.GetLabelSize())

def writePdf(label = "", oLabel = "", iLabel = "",
             oMap = {}, iMap = {}, innerEvent = {}) :

    outer = oMap.values()
    inner = iMap.keys()
    gr = graph(categories(outer = outer, inner = inner))
    null = r.TH2D("null", "%s;time (minutes)"%label,
                  1, 0.0, 1.1*minutes(*max(outer+inner)),
                  3, 0.5, 3.5)

    canvas = r.TCanvas()
    canvas.SetLeftMargin(0.25)
    canvas.SetTickx()
    canvas.SetTicky()

    null.Draw()
    nBoth = len(filter(lambda x:x!=None,innerEvent.values()))
    labelAxis(null, labels = {1:"only %s (%d)"%(iLabel, len(iMap)-nBoth),
                              2:"only %s (%d)"%(oLabel, len(oMap)-nBoth),
                              3:"both (%d)"%nBoth})

    gr.SetMarkerStyle(20)
    gr.Draw("psame")
    canvas.Print("%s.pdf"%label)
