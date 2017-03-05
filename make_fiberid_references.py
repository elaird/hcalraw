#!/usr/bin/env python

import os, sys
from configuration.patterns import rbxes, lineStart

#Generates .txt file in format same with oneRun.py from a list of RBXs

def WordStrip(iStr="", index=""): #iStr: input string, index: the index-th word in the string that you're looking for
    nWord = 0
    i=0
    while i < len(iStr):
       while iStr[i] == " ": 
        i+=1 #get to next word
        if i==len(iStr): break
       iStart = i
       while iStr[i] != " " and i < len(iStr): 
        i+=1
        if i==len(iStr): break
       nWord+=1
       if i==len(iStr): i = len(iStr)-1 #remove '/n' a the end of line
       if nWord == index: return iStr[iStart:i]
    
    return "#%s word not found in string: %s" %(index, iStr)


def WordSpace(iStr="", nSpace=""): 
    while len(iStr) < nSpace:   iStr = " " + iStr
    if len(iStr) == nSpace: return iStr
    else:   print "Error in fixing #char per word"
    

def DoubleSpace(iStr=""):
    oStr = []
    for i in range(0, len(iStr)):   oStr.append(iStr[i])
    return "  ".join(oStr)

def getKeyPosition(mapFileName = ""):
    keyPosition = {}
    keyPosition["RBXname"] = 8
    keyPosition["rm"] = 10
    keyPosition["rm_fib"] = 14
    keyPosition["fi_ch"] = 15
    
    if "HBEF" in mapFileName:
        keyPosition["htr_fib"] = 19
        keyPosition["spigo"] = 21
        keyPosition["fedid"] = 31
        keyPosition["crate"] = 16
        keyPosition["slot"] = 17

    if "HO" in mapFileName:
        keyPosition["htr_fib"] = 21
        keyPosition["spigo"] = 23
        keyPosition["fedid"] = 25
    if "CALIB" in mapFileName:
        keyPosition["RBXname"] = 7
        keyPosition["rm"] = 9
        keyPosition["rm_fib"] = 10
        keyPosition["fi_ch"] = 11
        keyPosition["htr_fib"] = 15
        keyPosition["spigo"] = 17
        keyPosition["fedid"] = 19
        
    return keyPosition
        
        

def ReformMap(iMapfile = "", ofile = "", oFileOpenMode = "w"):

    lines = open(iMapfile, "r").readlines() #opens & read the file
    output = open(ofile, oFileOpenMode)  #opens & write the file

    RBXnameRange = rbxes()

    rmRange = ['1','2','3','4']
    if "CALIB" in iMapfile: rmRange = ['4','5']
    keyPosition = getKeyPosition(iMapfile)

    for i in range(0, len(lines)):   #loop through Map file
        if "## file created" in lines[i]: continue  #over pass un_needed lines
        if "#   side    eta    phi   dphi" in lines[i]: continue
        current_line = lines[i]
    
        RBXname = WordStrip(current_line, keyPosition["RBXname"])
        rm = str(WordStrip(current_line, keyPosition["rm"]))
        rm_fib = str(WordStrip(current_line, keyPosition["rm_fib"]))
        fi_ch = str(WordStrip(current_line, keyPosition["fi_ch"]))
        htr_fib = str(WordStrip(current_line, keyPosition["htr_fib"]))
        if 'uHTR' in iMapfile:
            fedid = 'u' + str(WordStrip(current_line, keyPosition["crate"]))
            spigo = str(WordStrip(current_line, keyPosition["slot"]))

        else:
            fedid = str(WordStrip(current_line, keyPosition["fedid"]))
            spigo = str(WordStrip(current_line, keyPosition["spigo"]))

        spigo = WordSpace(spigo,2)
        htr_fib = WordSpace(htr_fib,2)
    
        if RBXname in RBXnameRange:
            if rm in rmRange and fi_ch == "0": #save only once per 3 channels
                output.writelines("%s%3s %02d %02d: %s %1d %1d\n" % (lineStart, fedid, int(spigo), int(htr_fib), RBXname, int(rm), int(rm_fib)))

    output.close()


def phase0():
    version = 'G'
    dir = "/afs/cern.ch/cms/HCAL/document/Mapping/Hua/2015-mar-4/"

    for gen, stems in [("vme", ["HCALmapHO", "HCALmapHBEF", "HCALmapCALIB"]),
                       ("utca", ["HCALmapHBEF_uHTR"]),
                       ]:
        oFileName = "data/ref_%s_%s.txt" % (gen, version)
        for i, stem in enumerate(stems):
            if stem.endswith("uHTR"):
                fileName = stem.replace("uHTR", "%s_uHTR.txt" % version)
            else:
                fileName = "%s_%s.txt" % (stem, version)

            fileName = "%s/%s" % (dir, fileName)
            print "Reading", fileName

            if i:
                ReformMap(iMapfile=fileName, ofile=oFileName, oFileOpenMode="a")
            else:
                ReformMap(iMapfile=fileName, ofile=oFileName)

        # sort
        sName = "%s_sorted" % oFileName
        os.system("sort -g %s > %s" % (oFileName, sName))
        os.system("mv %s %s" % (sName, oFileName))
        print "sorted reference file saved: %s" % oFileName


def ngReformMap(iMapfile="", ofile="", oFileOpenMode="w", rbx_whitelist=None, h_rbx="rbx", h_rmFi="rm_fi"):

    valid_rbxes = rbx_whitelist if rbx_whitelist else rbxes()

    output = open(ofile, oFileOpenMode)  #opens & write the file

    lines = open(iMapfile, "r").readlines()
    columns = lines[0].split()

    # BE
    iCrate = columns.index("crate")
    iSlot = columns.index("uhtr")
    iUf = columns.index("uhtr_fib")
    iFc = columns.index("fib_ch")

    # FE
    iRbx = columns.index(h_rbx)
    iRm = columns.index("rm")
    iRf = columns.index(h_rmFi)

    for iLine, line in enumerate(lines):
        if not iLine or line[0] == "#":
            continue

        fields = line.split()
        if fields[1] == "N/C":
            print "hacking line %d" % (1 + iLine)
            fields = fields[:3] + ["8"] + fields[3:]

        if len(fields) != len(columns):
            print "problem on line %d: %d fields vs. %d columns" % (1 + iLine, len(fields), len(columns))
            print columns
            print fields
            for i in range(min(len(fields), len(columns))):
                print i, columns[i], fields[i]
            sys.exit()

        # BE
        crate = int(fields[iCrate])
        slot = int(fields[iSlot])
        uhtr_fib = int(fields[iUf])

        # FE
        rbx = fields[iRbx]
        rm = int(fields[iRm])
        rm_fib = int(fields[iRf])

        if rbx in valid_rbxes:
            if fields[iFc] == "0":
                output.writelines("%su%2d %02d %02d: %s %1d %1d\n" % (lineStart, crate, slot, uhtr_fib, rbx, rm, rm_fib))

    output.close()


def ngHFMap(iMapfile="", ofile="", oFileOpenMode="w"):
    valid_rbxes = rbxes()

    output = open(ofile, oFileOpenMode)  #opens & write the file

    lines = open(iMapfile, "r").readlines()
    columns = lines[0].split()

    # BE
    iCrate = columns.index("Crate")
    iSlot = columns.index("uHTR")
    iUf = columns.index("uHTR_FI")
    iFc = columns.index("FI_CH")

    # FE
    iRbx = columns.index("ngRBX")
    iRm = columns.index("QIE10")
    iTb = columns.index("QIETB")
    iQf = columns.index("QIEFI")

    for iLine, line in enumerate(lines):
        if not iLine or line[0] == "#":
            continue

        fields = line.split()
        if len(fields) != 1 + len(columns):
            print "problem on line %d: %d fields vs. %d columns" % (1 + iLine, len(fields), len(columns))
            print columns
            print fields
            for i in range(min(len(fields), len(columns))):
                print i, columns[i], fields[i]
            sys.exit()

        # BE
        crate = int(fields[iCrate])
        slot = int(fields[iSlot])
        uhtr_fib = int(fields[iUf])

        # FE
        rbx = fields[iRbx]
        rm = int(fields[iRm])
        rm_fib = int(fields[iQf]) - 4

        if rbx in valid_rbxes:
            if fields[iFc] == "0":
                output.writelines("%su%2d %02d %02d: %s %1d %1d\n" % (lineStart, crate, slot, uhtr_fib, rbx, rm, rm_fib))

    output.close()


def plan1():
    # fileName = "/afs/cern.ch/cms/HCAL/document/Mapping/HBHE/ngHBHE/ngHE/ngHEP17/HBHEP17_template.txt"
    fileName = "data/HBHEP17_template.txt"
    oFileName = "data/ref_plan1.txt"
    ngReformMap(iMapfile=fileName, ofile=oFileName, oFileOpenMode="w", rbx_whitelist=["HBP17", "HEP17"], h_rbx="RBX", h_rmFi="rm_fib")

    sName = "%s_sorted" % oFileName
    os.system("sort -g %s > %s" % (oFileName, sName))
    os.system("mv %s %s" % (sName, oFileName))
    print "sorted reference file saved: %s" % oFileName


def ngHF():
    fileName = "ngHF2017LMap_20170125_pre04.tsv"
    oFileName = "data/ref_ngHF.txt"
    ngHFMap(iMapfile=fileName, ofile=oFileName, oFileOpenMode="w")

    sName = "%s_sorted" % oFileName
    os.system("sort -g %s > %s" % (oFileName, sName))
    os.system("mv %s %s" % (sName, oFileName))
    print "sorted reference file saved: %s" % oFileName


def calib():
    fileName = "HCALmapCALIB_H-RBX.tsv"
    oFileName = "data/ref_calib.txt"
    ngReformMap(iMapfile=fileName, ofile=oFileName, oFileOpenMode="w")

    sName = "%s_sorted" % oFileName
    os.system("sort -g %s > %s" % (oFileName, sName))
    os.system("mv %s %s" % (sName, oFileName))
    print "sorted reference file saved: %s" % oFileName


if __name__ == "__main__":
    # phase0()
    # plan1()
    # ngHF()
    calib()
