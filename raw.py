import utils
r = utils.ROOT()

from configuration import sw
import decode
import printer


def tchain(spec, cacheSizeMB=None):
    chain = r.TChain(spec["treeName"])
    for fileName in spec["fileNames"]:
        chain.Add(fileName)

    if cacheSizeMB:
        chain.SetCacheSize(cacheSizeMB * 1024**2)

    if spec["treeName"] == "Events":  # CMS CDAQ
        chain.SetBranchStatus("*", 0)
        found = False
        for branch in spec["rawCollections"]:
            if sw.use_fwlite:
                for suffix in [".obj", ".present"]:
                    branch1 = branch + suffix
                    if chain.GetBranch(branch1):
                        chain.SetBranchStatus(branch1, 1)
                        found = True
                    else:
                        printer.info("Could not find branch %s" % branch1)
            else:
                if chain.GetBranch(branch):
                    chain.SetBranchStatus(branch, 1)
                    found = True
                else:
                    printer.info("Could not find branch %s" % branch)
            if found:
                spec["rawCollection"] = branch
                break

        if not found:
            sys.exit("Could not find any branches: see configuration/sw.py")

    return chain


def pruneFeds(chain, s, uargs):
    wargs = {}

    remove = {}
    for fedId in s["fedIds"]:
        wargs[fedId] = {"tree": chain}
        if s["treeName"] == "Events":  # CMS CDAQ
            wfunc = wordsOneFed
            wargs[fedId].update({"fedId": fedId,
                                 "collection": s["rawCollection"],
                                 "product": sw.use_fwlite})
        elif s["treeName"] == "CMSRAW":  # HCAL local
            wfunc = wordsOneChunk
            wargs[fedId]["branch"] = s["branch"](fedId)
        else:
            wfunc = wordsOneBranch
            wargs[fedId]["branch"] = s["branch"](fedId)

        raw = wfunc(**wargs[fedId])
        if raw:
            if not unpacked(fedData=raw, **uargs).get("nBytesSW"):
                remove[fedId] = "read zero bytes"
        else:
            remove[fedId] = "no branch %s" % wargs[fedId].get("branch")

    for fedId, msg in sorted(remove.iteritems()):
        del wargs[fedId]
        printer.warning("removing FED %4d from spec (%s)." % (fedId, msg))
    if remove:
        printer.warning("No data from FED%s %s" % ("s" if 2 <= len(remove) else "", utils.shortList(remove.keys())))

    if wargs:
        del s["fedIds"]
        s["fedId0"] = sorted(wargs.keys())[0]
        for v in ["wfunc", "wargs"]:
            s[v] = eval(v)
    elif s["treeName"] == "Events":
        sys.exit("No listed FEDs had any data.")
    else:
        sys.exit(branches(chain))


def collected(tree=None, specs={}):
    raw = {}
    kargs = {}
    for item in ["dump", "unpack", "nBytesPer", "skipWords64"]:
        kargs[item] = specs[item]

    for fedId, wargs in sorted(specs["wargs"].iteritems()):
        raw[fedId] = unpacked(fedData=specs["wfunc"](**wargs),
                              warn=specs["warnUnpack"],
                              **kargs)

    raw[None] = {"iEntry": tree.GetReadEntry()}
    for key in ["label", "dump", "crateslots"]:
        raw[None][key] = specs[key]

    return raw


def w64(fedData, jWord64, nBytesPer):
    if nBytesPer == 1:
        offset = 8*jWord64
        bytes = [fedData.at(offset+iByte) for iByte in range(8)]
        word64 = struct.unpack('Q', "".join(bytes))[0]
        #like above with 'B'*8 rather than 'Q':
        #b = [ord(fedData.at(offset+iByte)) for iByte in range(8)]
    elif nBytesPer == 4:
        word64 = fedData.at(2*jWord64)
        word64 += fedData.at(2*jWord64 + 1) << 32
    elif nBytesPer == 8:
        word64 = fedData.at(jWord64)
    return word64


def unpackedHeader(spec):
    wargs = spec["wargs"][spec["fedId0"]]
    return unpacked(fedData=spec["wfunc"](**wargs),
                    nBytesPer=spec["nBytesPer"],
                    skipWords64=spec["skipWords64"],
                    headerOnly=True)


# for format documentation, see decode.py
def unpacked(fedData=None, nBytesPer=None, headerOnly=False, unpack=True,
             warn=True, skipWords64=[], dump=-99):
    assert fedData
    assert nBytesPer in [1, 4, 8], "ERROR: invalid nBytes per index (%s)." % str(nBytesPer)

    header = {"iWordPayload0": 6,
              "utca": None,
              }  # modified by decode.header
    trailer = {}
    other = {}
    htrBlocks = {}

    nWord64Trailer = 1

    nWord64 = fedData.size()*nBytesPer/8
    nWord16Skipped = 0

    nToSkip = len(set(skipWords64))
    skipped64 = []

    for jWord64 in range(nWord64):
        if not unpack:
            continue

        word64 = w64(fedData, jWord64, nBytesPer)

        if jWord64 in skipWords64:
            skipped64.append(word64)
            continue

        iWord64 = jWord64 - len(skipped64)

        if 9 <= dump:
            if not iWord64:
                print "#iw64 w64"
            print "%5d" % iWord64, "%016x" % word64

        if iWord64 < header["iWordPayload0"]:
            decode.header(header, iWord64, word64)
            if header.get("uFoV"):
                nWord64Trailer = 2  # accommodate block trailer
            iWordTrailer0 = nWord64 - nToSkip - nWord64Trailer
        elif headerOnly:
            break
        elif iWord64 < iWordTrailer0:
            for i in range(4):
                word16 = (word64 >> (16*i)) & 0xffff
                iWord16 = 4*iWord64+i
                returnCode = decode.payload(htrBlocks,
                                            iWord16=iWord16,
                                            word16=word16,
                                            word16Counts=header["word16Counts"],
                                            utca=header["utca"],
                                            fedId=header["FEDid"],
                                            warn=warn,
                                            dump=dump)
                if returnCode is None:
                    continue

                # ignore VME pad words (zero)
                if not header["utca"] and iWord64 + 1 == iWordTrailer0:
                    if 4 * header["iWordPayload0"] + sum(header["word16Counts"]) <= iWord16:
                        if not word16:
                            continue

                nWord16Skipped += 1
                if warn:
                    printer.warning(" ".join(["skipping",
                                              "FED %d" % header["FEDid"],
                                              "event %d" % header["EvN"],
                                              "iWord16 %d" % iWord16,
                                              "word16 0x%04x" % word16,
                                              ]))
        else:
            if "htrIndex" in htrBlocks:
                del htrBlocks["htrIndex"]  # fixme

            if header["uFoV"] and (iWord64 == nWord64 - nToSkip - 2):
                decode.block_trailer_ufov1(trailer, iWord64, word64)
            else:
                decode.trailer(trailer, iWord64, word64)

    decode.other(other, skipped64)

    return {"header": header,
            "trailer": trailer,
            "htrBlocks": htrBlocks,
            "other": other,
            "nBytesSW": 8*nWord64,
            "nWord16Skipped": nWord16Skipped,
            }


def charsOneFed(tree=None, fedId=None, collection="", product=None):
    FEDRawData = getattr(tree, collection)
    if product:
        FEDRawData = FEDRawData.product()
    return r.FEDRawDataChars(FEDRawData.FEDData(fedId))


def wordsOneFed(tree=None, fedId=None, collection="", product=None):
    FEDRawData = getattr(tree, collection)
    if product:
        FEDRawData = FEDRawData.product()
    return r.FEDRawDataWords(FEDRawData.FEDData(fedId))


def wordsOneChunk(tree=None, branch=""):
    chunk = wordsOneBranch(tree, branch)
    if chunk is None:
        return chunk
    else:
        return r.CDFChunk2(chunk)


def wordsOneBranch(tree=None, branch=""):
    try:
        chunk = getattr(tree, branch)
    except AttributeError:
        chunk = None
    return chunk


def branches(tree):
    names = [item.GetName() for item in tree.GetListOfBranches()]
    msg = ["These branches are available:"] + sorted(names)
    return "\n".join(msg)
