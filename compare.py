import printRaw

def bcnLabel(delta = 0) :
    out = "BcN"
    if delta<0 :
        out += " - %d"%abs(delta)
    elif delta>0 :
        out += " + %d"%abs(delta)
    return out

def singleFedPlots(raw = {}, fedId = None, book = {}) :
    if fedId==None : return
    d = raw[fedId]
    book.fill(d["TTS"], "TTS_%d"%fedId, 16, -0.5, 15.5, title = "FED %d; TTS state;Events / bin"%fedId)

    caps = {0:0, 1:0, 2:0, 3:0}
    ErrF = {0:0, 1:0, 2:0, 3:0}
    for block in d["htrBlocks"].values() :
        for channelId,channelData in block["channelData"].iteritems() :
            ErrF[channelData["ErrF"]] += 1
            if not channelData["ErrF"] :
                caps[channelData["CapId0"]] += 1
    errFSum = 0.0+sum(ErrF.values())
    if errFSum :
        book.fill(ErrF[0]/errFSum, "ErrF0_%d"%fedId, 44, 0.0, 1.1, title = "FED %d;frac. chan. w/ErrF==0"%fedId)

    capSum = 0.0+sum(caps.values())
    if capSum :
        book.fill(max(caps.values())/capSum, "PopCapFrac_%d"%fedId, 44, 0.0, 1.1,
                  title = "FED %d;frac. ErrF=0 chans w/most pop. capId"%fedId)

def compare(raw1 = {}, raw2 = {}, book = {}) :
    hyphens = True
    if raw1 and raw1[None]["printRaw"] :
        printRaw.oneEvent(raw1, hyphens)
        hyphens = False
    if raw2 and raw2[None]["printRaw"] :
        printRaw.oneEvent(raw2, hyphens)

    for raw in [raw1, raw2] :
        for fedId,dct in raw.iteritems() :
            singleFedPlots(raw, fedId, book)

    #mapF1,mapB1 = dataMap(raw1)
    #mapF2,mapB2 = dataMap(raw2)
    #stats = matchStats(mapF1, mapB2)
    #report(*stats)

    #some delta plots
    fed1 = 989
    fed2 = 714
    d1 = raw1.get(fed1, {})
    d2 = raw2.get(fed2, {})
    if d1 and d2 :
        bcnXTitle = "FED %d %s - FED %d %s"%(fed1, bcnLabel(raw1[None]["bcnDelta"]),
                                             fed2, bcnLabel(raw2[None]["bcnDelta"]))
        book.fill(d1["BcN"]-d2["BcN"], "deltaBcN", 11, -5.5, 5.5, title = ";%s;Events / bin"%bcnXTitle)
        book.fill(d1["OrN"]-d2["OrN"], "deltaOrN", 11, -5.5, 5.5, title = ";FED %s OrN - FED %s OrN;Events / bin"%(fed1, fed2))
        book.fill(d1["EvN"]-d2["EvN"], "deltaEvN", 11, -5.5, 5.5, title = ";FED %s EvN - FED %s EvN;Events / bin"%(fed1, fed2))

def coordString(fedId, moduleId, fiber, channel) :
    return "%3d %2d %2d %2d"%(fedId, moduleId, fiber, channel)

def report(matched = {}, failed = []) :
    print "MATCHED fibers %d:"%len(matched)
    print "uTCA --> CMS"
    print "(fed  h  f ch) --> (fed  h  f ch)"
    print "---------------------------------"
    for k in sorted(matched.keys()) :
        print "(%s) --> (%s)"%(coordString(*k), coordString(*matched[k]))

    print
    print "CMS --> uTCA"
    print "(fed  h  f ch) --> (fed  h  f ch)"
    print "---------------------------------"
    lines = []
    for k,v in matched.iteritems() :
        lines.append("(%s) --> (%s)"%(coordString(*v), coordString(*k)))
    for l in sorted(lines) :
        print l

    print
    print "FAILED fibers %d:"%len(failed)
    if failed :
        print "(fed  h  f ch)"
        print "--------------"
        for c in sorted(failed) :
            print "(%s)"%coordString(*c)

def matchStats(f = {}, b = {}) :
    matched = {}
    failed = []
    for coords,data in f.iteritems() :
        if data in b :
            matched[coords] = b[data]
        else :
            failed.append(coords)
    return matched,failed

def dataMap(raw = {}) :
    forward = {}
    backward = {}

    fiberMap = raw[None]["fiberMap"]
    for fedId,d in raw.iteritems() :
        if fedId==None : continue
        if fedId==714 :
            matchRange = raw[None]["hbheMatchRange"]
        if fedId==722 :
            matchRange = raw[None]["hfMatchRange"]

        for key,block in d["htrBlocks"].iteritems() :
            if fedId==989 :
                moduleId = block["ModuleId"]&0xf
                if moduleId<=4 :
                    matchRange = raw[None]["hbheMatchRange"]
                else :
                    matchRange = raw[None]["hfMatchRange"]
            else :
                moduleId = block["ModuleId"]&0x1f

            for channelId,channelData in block["channelData"].iteritems() :
                channel = channelId%4
                fiber = 1+channelId/4 #integer division
                fiber = fiberMap[fiber] if fiber in fiberMap else fiber
                if channel!=1 : continue
                coords = (fedId, moduleId, fiber, channel)
                qie = channelData["QIE"]
                if len(qie)<len(matchRange) :
                    #print "skipping bogus channel",coords
                    continue
                data = tuple([qie[i] for i in matchRange])
                #print coords,matchRange,[hex(d) for d in data]
                forward[coords] = data
                backward[data] = coords
    return forward,backward
