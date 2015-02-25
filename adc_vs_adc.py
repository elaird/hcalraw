#!/usr/bin/env python

import ROOT as r


def entitle(hSum, skip_rxs, skip_evnOKs):
    if hSum:
        title = []
        if skip_rxs:
            title.append("PPOD RXes" +  ",".join(["%2d/%1d" % (sl, rx) for (cr, sl, rx) in skip_rxs]))
        if skip_evnOKs == [0]:
            title.append("mismatched EvN")

        if not title:
            hSum.SetTitle("all channels")
        else:
            hSum.SetTitle("excluding: %s " % "#semicolon ".join(title))


def histo(fileName="", skip_rxs=[], skip_evnOKs=[]):
    hSum = None
    f = r.TFile(fileName)
    for cr in [22]:
        for sl in range(1, 13):
            for rx in range(2):
                if (cr, sl, rx) in skip_rxs:
                    continue

                for evnOK in range(2):
                    if evnOK in skip_evnOKs:
                        continue

                    h = f.Get("adc_vs_adc_EvNOK%1d_cr%02d_sl%02d_rx%1d" % (evnOK, cr, sl, rx))
                    if not h:
                        continue

                    if hSum is None:
                        hSum = h.Clone("adc_vs_adc")
                        hSum.Reset()
                        hSum.SetDirectory(0)
                    hSum.Add(h)

    entitle(hSum, skip_rxs, skip_evnOKs)
    return hSum


def draw(h, title=""):
    h.SetStats(False)
    h.Draw("colz")
    h.GetXaxis().SetTitle("ADC (VME FEDs 718,719)")
    h.GetYaxis().SetTitle("ADC (uTCA FED 1118)")
    h.GetZaxis().SetTitle("samples / bin")
    if title:
        h.SetTitle(title)

    for x in ["X", "Y", "Z"]:
        ax = getattr(h, "Get%saxis" % x)()
        ax.SetTitleOffset(1.3)
        #ax.CenterTitle()

    m = 0.15
    r.gPad.SetTopMargin(m)
    r.gPad.SetBottomMargin(m)
    r.gPad.SetLeftMargin(m)
    r.gPad.SetRightMargin(m)
    r.gPad.SetTickx()
    r.gPad.SetTicky()
    r.gPad.SetLogz()


def go(fileName="output/latest.root", exclude=None):
    r.gROOT.SetBatch(True)

    skip_rxs = [(22,  4, 0),
                (22, 10, 0),
                (22, 11, 0),
                ] if exclude else []

    skip_evnOKs = []

    h = histo(fileName, skip_rxs=skip_rxs, skip_evnOKs=skip_evnOKs)

    if h:
        can = r.TCanvas("canvas", "canvas", 1600, 1600)
        draw(h)

        yx = r.TF1("yx", "x", h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax())
        yx.SetLineColor(r.kBlack)
        yx.SetLineWidth(1)
        yx.Draw("same")

        leg = r.TLegend(0.2, 0.7, 0.35, 0.85)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.AddEntry(yx, "y = x", "l")
        leg.Draw()

        r.gPad.Update()
        pdf = fileName.replace(".root", "_scatter.pdf")
        if exclude:
            pdf = pdf.replace(".pdf", "_exclude.pdf")
        r.gPad.Print(pdf)
    else:
        print "No histograms matching selection were found."


if __name__ == "__main__":
    go()
