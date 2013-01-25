#see http://ohm.bu.edu/~hazen/CMS/SLHC/HcalUpgradeDataFormat_v1_2_2.pdf

def bcn(raw, delta = 0) :
    if not delta : return raw
    out = raw + delta
    if out<0    : out += 3564
    if out>3563 : out -= 3564
    return out

def trailer(d = {}, iWord64 = None, word64 = None, bcnDelta = 0) :
    d["TTS"] = (word64&0xf)>>2
    d["nWord64"] = (word64&(0xffffff<<32))>>32

def header(d = {}, iWord64 = None, word64 = None, bcnDelta = 0) :
    b = [((0xff<<8*i) & word64)>>8*i for i in range(8)]

    if iWord64==0 :
        #d["eight"] = 0xf & b[0]
        #d["fov"] = (0xf0 & b[0])/(1<<4)
        d["FEDid"] = (0xf & b[2])*(1<<8) + b[1]
        d["BcN"] = (0xf0 & b[2])/(1<<4) + b[3]*(1<<4)
        d["EvN"] = b[4] + b[5]*(1<<8) + b[6]*(1<<16)
        d["BcN"] = bcn(d["BcN"], bcnDelta)
        #d["evtTy"] = 0xf & b[7]
        #d["five"] = (0xf0 & b[7])/(1<<4)

    if iWord64==1 :
        #d["zero1"] = 0xf & b[0]
        d["OrN"] = (0xf0 & b[0])/(1<<4) + b[1]*(1<<4) + b[2]*(1<<12) + b[3]*(1<<20) + (0xf & b[4])*(1<<28)

    uhtr = {3:0, 4:4, 5:8}
    if iWord64 in uhtr :
        uhtr0 = uhtr[iWord64]
        for i in range(4) :
            key = "uHTR%d"%(uhtr0+i)
            b0 = b[  2*i]
            b1 = b[1+2*i]
            d[key] = {"E":(b1&80)>>6,
                      "P":(b1&40)>>5,
                      "C":(b1&20)>>4,
                      "V":(b1&10)>>3,
                      "nWord16":(b1 & 0xf)*(1<<4) + b0,
                      }

def payload(d = {}, iWord16 = None, word16 = None, bcnDelta = 0) :
    w = word16
    if "iWordZero" not in d :
        d["iWordZero"] = iWord16
        d[d["iWordZero"]] = {}

    l = d[d["iWordZero"]]
    i = iWord16 - d["iWordZero"]
    if i==0 :
        l["InputID"] = (w&0xf0)/(1<<8)
        l["EvN"] = w&0xf
    if i==1 :
        l["EvN"] += w*(1<<8)
    if i==3 :
        l["ModuleId"] = w&0x7ff
        l["OrN"] = (w&0xf800)>>11
    if i==4 :
        l["BcN"] = bcn(w&0xfff, bcnDelta)
        l["FormatVer"] = (w&0xf000)>>12
    if i==5 :
        #l["nWord16"] = w&0x3fff
        l["nWord16"] = 228
        l["channelData"] = {}
    if i<=5 : return

    if w&(1<<15) :
        channelId = w&0xff
        #l["channelData"][channelId] = {"Flavor":(w&7000)>>12,
#                                       }
    else :
        pass

    if i==l["nWord16"]-1 :
        del d["iWordZero"]
