import decode
import printer
import struct
from configuration.sw import histo_fed

def unpack(raw1={}, raw2={}, chain=None, chainI=None, outer={}, inner={}, **_):
    raw1.update(collected(tree=chain, specs=outer))
    if inner:
        raw2.update(collected(tree=chainI, specs=inner))


def collected(tree=None, specs={}):
    raw = {}
    kargs = {}
    for item in ["dump", "lastNAmcs", "nBytesPer", "skipWords64"]:
        kargs[item] = specs[item]

    for fedId, wargs in sorted(specs["wargs"].items()):
        raw[fedId] = unpacked(fedData=specs["wfunc"](**wargs),
                              warn=specs["warnQuality"],
                              **kargs)

    raw[None] = {"iEntry": tree.GetReadEntry()}
    for key in ["label", "dump", "crateslots", "firstNTs", "perTs"]:
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
def unpacked(fedData=None, nBytesPer=None, headerOnly=False,
             warn=True, skipWords64=[], dump=-99, lastNAmcs=0):
    assert fedData
    assert nBytesPer in [1, 4, 8], "ERROR: invalid nBytes per index (%s)." % str(nBytesPer)

    header = {"iWordPayload0": 6,
              "utca": None,
              }  # modified by decode.header
    trailer = {}
    other = {}
    htrBlocks = {}

    nWord64Trailer = 1

    nWord64 = fedData.size() * nBytesPer // 8
    nWord16Skipped = 0

    nToSkip = len(set(skipWords64))
    skipped64 = []

    for jWord64 in range(nWord64):
        word64 = w64(fedData, jWord64, nBytesPer)

        if jWord64 in skipWords64:
            skipped64.append(word64)
            continue

        iWord64 = jWord64 - len(skipped64)

        if 12 <= dump:
            if not iWord64:
                print("#iw64 w64")
            print("%5d" % iWord64, "%016x" % word64)

        if iWord64 < header["iWordPayload0"]:
            decode.header(header, iWord64, word64, lastNAmcs)
            if header.get("uFoV"):
                nWord64Trailer = 2  # accommodate block trailer
            iWordTrailer0 = nWord64 - nToSkip - nWord64Trailer
            if iWord64 == 1 and not header["OrN"]:
                if headerOnly:
                    break
                else:
                    return unpacked_sw_fed(fedData, header, nBytesPer, dump)
        elif headerOnly:
            break
        elif lastNAmcs and iWord64 < header["iWordPayloadn"]:
            continue
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


def unpacked_sw_fed(fedData, header, nBytesPer, dump):
    fedId = header["FEDid"]
    if histo_fed(fedId):
        return unpacked_histo(fedData, fedId, nBytesPer, dump)
    else:
        printer.error("Unpacking of software FED %d is not implemented." % fedId)
        nBytesSW = fedData.size() * nBytesPer
        return {"header": header,
                "trailer": {"nWord64": nBytesSW // 8},
                "other": {},
                "nBytesSW": nBytesSW,
               }


# for format documentation, see decode.py
def unpacked_histo(fedData, fedId, nBytesPer, dump):
    assert fedData
    assert nBytesPer in [1, 4, 8], "ERROR: invalid nBytes per index (%s)." % str(nBytesPer)

    header = {}
    trailer = {}
    histograms = {}
    iPayload0 = 4

    nWord64 = fedData.size() * nBytesPer // 8
    for iWord64 in range(nWord64):
        word64 = w64(fedData, iWord64, nBytesPer)

        if 12 <= dump:
            if not iWord64:
                print("#iw64 w64")
            print("%5d" % iWord64, "%016x" % word64)

        if iWord64 < 2:
            decode.header(header, iWord64, word64)

        if iWord64 < iPayload0:
            for i in range(2):
                word32 = (word64 >> (32*i)) & 0xffffffff
                iWord32 = 2 * (iWord64 - 2) + i
                decode.header_histo(header, iWord32, word32)
            continue

        if iWord64 == nWord64 - 1:
            decode.trailer(trailer, iWord64, word64)
            continue

        nWords32PerChannel = 2 + header["nBins"]
        for i in range(2):
            word32 = (word64 >> (32*i)) & 0xffffffff
            iWord32 = 2 * (iWord64 - iPayload0) + i
            jWord32 = iWord32 % nWords32PerChannel
            key = iWord32 // nWords32PerChannel
            if key not in histograms:
                histograms[key] = {}
            d = histograms[key]
            decode.histo(d, jWord32, word32)

    return {"header": header,
            "trailer": trailer,
            "histograms": histograms,
            "other": {},
            "nBytesSW": 8 * nWord64,
            "nWord16Skipped": 0,
           }
