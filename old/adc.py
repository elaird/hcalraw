#!/usr/bin/env python

import ROOT as r

def histo(fileName="", hName=""):
    f = r.TFile(fileName)
    h = f.Get(hName)
    assert h
    h.SetDirectory(0)
    f.Close()
    return h


def onePlot(n="1k", h=""):
    assert h
    h_10 = histo("output/221348_%s.root" % n, h)
    h_16 = histo("output/221351_%s.root" % n, h)
    h_ped = histo("output/221353_%s.root" % n, h)
    
    leg = r.TLegend(0.45, 0.65, 0.75, 0.85)
    
    h_ped.SetLineColor(r.kBlack)
    h_ped.Draw("ehist")
    yTitle = h_ped.GetYaxis().GetTitle()
    h_ped.GetYaxis().SetTitle(yTitle + " ( / %s events)" % n)
    h_ped.GetXaxis().SetRangeUser(0.0, 32.0)
    leg.AddEntry(h_ped, "pedestal", "lpe")
    
    r.gPad.SetLogy()
    r.gPad.SetTickx()
    r.gPad.SetTicky()
    
    h_10.SetLineColor(r.kBlue)
    h_10.Draw("ehistsame")
    leg.AddEntry(h_10, "self-trigger (10 fC)", "lpe")
    
    h_16.SetLineColor(r.kRed)
    h_16.Draw("ehistsame")
    leg.AddEntry(h_16, "self-trigger (16 fC)", "lpe")
    
    leg.Draw()
    r.gPad.Print("%s.png" % h)

if __name__ == "__main__":    
    r.gStyle.SetOptStat(1110)
    for h in ["max_adc", "all_adc"]:
        onePlot(h=h)

