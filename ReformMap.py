#!/usr/bin/env python

#Generates .txt file in formatt same with oneRun.py from a list of RBXs

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
        
        

def ReformMap(iMapfile = "", iListfile = "", ofile = "", oFileOpenMode = "w"):

    lines = open(iMapfile, "r").readlines() #opens & read the file
    output = open(ofile, oFileOpenMode)  #opens & write the file

    ListLines = open(iListfile, "r").readlines()

    subdet = []
    for i in range(0, len(ListLines)): #store subdet names
        current_line = ListLines[i]
        subdet.append(current_line[0:current_line.find(",")])

    RBXnameRange = subdet
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
                if len(RBXname)==5: outline = fedid + " " + spigo + " " + htr_fib + ":  " + RBXname + "  " + rm + " " + rm_fib + "\n"
                else: outline = fedid + " " + spigo + " " + htr_fib + ":  " + RBXname + " " + rm + " " + rm_fib + "\n"
                output.writelines(outline)

    output.close()   

version = 'G'
dir = "references"
ReformMap(iMapfile = "%s/HCALmapHO_%s.txt" %(dir, version), iListfile = "%s/CCM_numbers.txt" %dir, ofile = "all_Map_%s.txt" %version) 
ReformMap(iMapfile = "%s/HCALmapHBEF_B.txt" %dir, iListfile = "%s/CCM_numbers.txt" %dir, ofile = "all_Map_%s.txt" %version, oFileOpenMode = "a") 
ReformMap(iMapfile = "%s/HCALmapCALIB_A.txt" %dir, iListfile = "%s/CCM_numbers.txt" %dir, ofile = "all_Map_%s.txt" %version, oFileOpenMode = "a")
ReformMap(iMapfile = "%s/HCALmapHBEF_E_uHTR.txt" %dir, iListfile = "%s/CCM_numbers.txt" %dir, ofile = "all_Map_%s.txt" %version, oFileOpenMode = "a")