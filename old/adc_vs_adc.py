import ROOT as r


def entitle(hSum, skip_rxs):
    if hSum:
        title = []
        if skip_rxs:
            title.append("PPOD RXes" +  ",".join(["%2d/%1d" % (sl, rx) for (cr, sl, rx) in skip_rxs]))

        if title:
            hSum.SetTitle("excluding: %s " % "#semicolon ".join(title))

def i(s):
    return int(s[2:])


def histo(fileName="", skip_rxs=[], prefix=""):
    hSum = None
    f = r.TFile(fileName)
    for tkey in f.GetListOfKeys():
        name = tkey.GetName()
        if not name.startswith(prefix):
            continue

        # "adc_vs_adc_cr%02d_sl%02d_rx%1d"
        t = map(i, name.split("_")[3:])
        if t in skip_rxs:
            continue

        h = f.Get(name)
        if hSum is None:
            hSum = h.Clone(prefix)
            hSum.Reset()
            hSum.SetDirectory(0)
        hSum.Add(h)

    entitle(hSum, skip_rxs)
    return hSum


def fedString(lst=[]):
    return ",".join(["%d" % i for i in lst])


def draw(h, feds1=[], feds2=[], prefix=""):
    P = prefix[:prefix.find("_vs_")].upper()

    h.SetStats(False)
    h.Draw("colz")
    h.GetXaxis().SetTitle("%s (FEDs %s)" % (P, fedString(feds1)))
    h.GetYaxis().SetTitle("%s (FEDs %s)" % (P, fedString(feds2)))
    h.GetZaxis().SetTitle("samples / bin")

    h.GetXaxis().SetTitleOffset(1.25)
    h.GetYaxis().SetTitleOffset(1.50)
    h.GetZaxis().SetTitleOffset(1.35)

    m = 0.15
    r.gPad.SetTopMargin(m)
    r.gPad.SetBottomMargin(m)
    r.gPad.SetLeftMargin(m)
    r.gPad.SetRightMargin(m)
    r.gPad.SetTickx()
    r.gPad.SetTicky()
    r.gPad.SetLogz()


def go(fileName="output/latest.root", exclude=None, feds1=[], feds2=[], prefix=""):
    assert prefix

    r.gROOT.SetBatch(True)

    skip_rxs = [(22,  4, 0),
                (22, 10, 0),
                (22, 11, 0),
                ] if exclude else []

    h = histo(fileName, skip_rxs=skip_rxs, prefix=prefix)

    if h:
        can = r.TCanvas("canvas", "canvas", 1600, 1600)
        draw(h, feds1=feds1, feds2=feds2, prefix=prefix)

        yx = r.TF1("yx", "x", h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax())
        yx.SetLineColor(r.kBlack)
        yx.SetLineWidth(1)
        yx.SetLineStyle(2)
        yx.Draw("same")

        leg = r.TLegend(0.2, 0.7, 0.35, 0.85)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.AddEntry(yx, "y = x", "l")
        leg.Draw()

        r.gPad.Update()
        pdf = fileName.replace(".root", "_%s.pdf" % prefix)
        if exclude:
            pdf = pdf.replace(".pdf", "_exclude.pdf")
        r.gPad.Print(pdf)
    else:
        print "No histograms matching selection (prefix %s) were found." % prefix
