def utca(uhtr=False):
    d2c = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
           7:   9,
           8:  11,
           9:  12,
           10: 10,
           11:  8,
           12:  7,
           }

    return {"label": "uTCA",
            "treeName": "CMSRAW",
            "format": "HCAL",
            "auxBranch": False,
            "utca": True,
            "branchName": "Chunk",
            "bcnDelta": -118,
            "fiberMap": {} if uhtr else d2c,
            "nEventsMax": None,
            "printSkip": {"fibCh": [0, 2],
                          "ErrF": [3],
                          },
            "unpackSkipFlavors": [4],
            "matchRange": {930: range(10),    # B904
                           931: range(10),    # B904
                           989: range(10),    # Jan. slice-test
                           990: range(1, 10), # Jan. slice-test (HF)
                           },
            "nPatternFibers": 6,
            "nPatternTs": 10,
            }


def cms(local=False):
    matchRange = {}
    for iFed in range(700, 732):
        matchRange[iFed] = range(10)
    matchRange[722] = range(9) # Jan. slice-test

    out = {"label": "CMS",
           "utca": False,
           "matchRange": matchRange,
           "bcnDelta": 0,
           "fiberMap": {},
           "nEventsMax": 3,
           "unpackSkipFlavors": [7],
           "printSkip": {"fibCh": [0, 2],
                         "ErrF": [3]},
           "nPatternFibers": 6,
           "nPatternTs": 10,
           }
    if local:
        out.update({"treeName": "CMSRAW",
                    "format":  "HCAL",
                    "auxBranch": False,
                    "branchName": "HCAL_DCC",
                    })
    else:
        out.update({"treeName": "Events",
                    "format":  "CMS",
                    "auxBranch": True,
                    "rawCollection": "FEDRawDataCollection_rawDataCollector__LHC",
                    })
    return out
