#!/usr/bin/env python


def opts(alsoArgs=False):
    import optparse
    import sys

    if alsoArgs:
        parser = optparse.OptionParser(usage="usage: %prog [options] args")
    else:
        parser = optparse.OptionParser()

    reqd = optparse.OptionGroup(parser, "REQUIRED")
    reqd.add_option("--file1",
                    dest="file1",
                    default="",
                    help=".root file over which to run")
    reqd.add_option("--feds1",
                    dest="feds1",
                    default="",
                    help="FEDs to use in file1, e.g. 714,722 or e.g. HBHE")
    parser.add_option_group(reqd)

    common = optparse.OptionGroup(parser, "Misc options")
    common.add_option("--nevents",
                      dest="nevents",
                      default="",
                      metavar="N",
                      help="Stop after N events (including skipped events).")
    common.add_option("--nevents-skip",
                      dest="neventsSkip",
                      default=0,
                      metavar="M",
                      help="Skip the first M events.")
    common.add_option("--output-file",
                      dest="outputFile",
                      default="output/latest.root",
                      metavar="f",
                      help="Store histograms in this .root file.")
    common.add_option("--no-loop",
                      dest="noLoop",
                      default=False,
                      action="store_true",
                      help="Plot from existing .root file (do not look at data).")
    common.add_option("--no-unpack",
                      dest="noUnpack",
                      default=False,
                      action="store_true",
                      help="Loop over raw data, but do not unpack it.")
    common.add_option("--skip-flavors",
                      dest="unpackSkipFlavors",
                      default="",
                      metavar="s",
                      help="Do not unpack channels with these flavors (e.g. 2,7).")
    common.add_option("--adc-plots",
                      dest="adcPlots",
                      default=False,
                      action="store_true",
                      help="Histogram ADC values when ErrF == 0.")
    common.add_option("--profile",
                      dest="profile",
                      default=False,
                      action="store_true",
                      help="Profile this program.")
    parser.add_option_group(common)

    printing = optparse.OptionGroup(parser, "Options for printing to stdout")
    printing.add_option("--no-color",
                        dest="noColor",
                        default=False,
                        action="store_true",
                        help="disable color in stdout")
    printing.add_option("--progress",
                        dest="progress",
                        default=False,
                        action="store_true",
                        help="print TTree entry number (when power of 2)")
    printing.add_option("--no-warn-unpack",
                        dest="noWarnUnpack",
                        default=False,
                        action="store_true",
                        help="suppress warnings during unpacking")
    printing.add_option("--crateslots",
                        dest="crateslots",
                        default=None,
                        metavar="D",
                        help="list of (100*crate)+slot to dump, e.g. 917,2911")

    dump = ["dump level (-1 to 8), default is -1.",
            "-1: only program info, warnings and errors",
            "0: only summary (no per-event info)",
            "1: DCC/AMC13 headers",
            "2: (u)HTR summary info",
            "3: (u)HTR headers",
            "4: data (channel=1, fibers with ErrF != 3)",
            "5: data (fibers with ErrF != 3); TPs (> 0)",
            "6: data (all); TPs (all)",
            "7: 64bit words; data (all); TPs (all)",
            "8: 64(+16)bit words; data (all); TPs (all)",
            ]
    printing.add_option("--dump",
                        dest="dump",
                        default=-1,
                        metavar="D",
                        help=" ".join([d.ljust(60) for d in dump]))
    parser.add_option_group(printing)

    match = optparse.OptionGroup(parser, "Options for matching events across files")
    match.add_option("--file2",
                     dest="file2",
                     default="",
                     help=".root file to compare with file1")
    match.add_option("--feds2",
                     dest="feds2",
                     default="",
                     help="FEDs to use in file2, e.g. 931")
    match.add_option("--filter-evn",
                     dest="filterEvn",
                     default=False,
                     action="store_true",
                     help="Consider only EvN with (EvN & 0x1fff) == 0.")
    match.add_option("--identity-map",
                     dest="identityMap",
                     default=False,
                     action="store_true",
                     help="Force use of identity map.")
    match.add_option("--print-event-map",
                     dest="printEventMap",
                     default=False,
                     action="store_true",
                     help="Print event map to stdout.")
    parser.add_option_group(match)

    matchCh = optparse.OptionGroup(parser, "Options for matching channels across events")
    matchCh.add_option("--match",
                       dest="match",
                       default="",
                       metavar="s",
                       help="choose configuration.matchRange_s")
    matchCh.add_option("--any-emap",
                       dest="anyEmap",
                       default=False,
                       action="store_true",
                       help="Brute-force search for matches.")
    matchCh.add_option("--print-emap",
                       dest="printEmap",
                       default=False,
                       action="store_true",
                       help="Print emap found with --any-emap.")
    parser.add_option_group(matchCh)

    patterns = optparse.OptionGroup(parser, "Options for decoding patterns")
    patterns.add_option("--patterns",
                        dest="patterns",
                        default=False,
                        action="store_true",
                        help="interpret QIE data as FE patterns")
    patterns.add_option("--nts",
                        dest="nts",
                        default=10,
                        metavar="N",
                        help="No. of time slices to consider (default is 10).")
    patterns.add_option("--patternB",
                        dest="patternB",
                        default=False,
                        action="store_true",
                        help="Consider also patterns mixed across fibers.")
    patterns.add_option("--rm-ribbon",
                        dest="rmRibbon",
                        default=False,
                        action="store_true",
                        help="Pair central 6 fibers (of 8 or 12).")
    parser.add_option_group(patterns)

    options, args = parser.parse_args()

    if alsoArgs:
        return options, args


    if not all([options.file1, options.feds1]):
        parser.print_help()
        sys.exit(1)
    if not options.outputFile.endswith(".root"):
        sys.exit("--output-file must end with .root (%s)" % options.outputFile)
    if options.feds2 and not options.file2:
        print "INFO: using --file1 also for --file2; also using identity map"
        options.file2 = options.file1
        options.identityMap = True

    return options


def integer(value="", tag=""):
    if value == '':
        return None

    try:
        return int(value)
    except ValueError:
        sys.exit("%s '%s' cannot be converted to an int." % (tag, value))


def checkModules():
    import types
    names = []
    for key, value in globals().iteritems():
        if isinstance(value, types.ModuleType):
            names.append(key)
    if names  not in [[], ["__builtins__"]]:
        print names
        print "Please put imports after this block, to prevent PyROOT from stealing '--help'."


def main(options, check=True):
    if check:
        checkModules()

    import analyze
    import configuration
    import printer
    import sys
    import cProfile
    import graphs

    if options.match:
        configuration.matchRange = getattr(configuration, "matchRange_%s" % options.match)
        configuration.matchRange()  # call once to set utcaBcnDelta

    if options.noColor:
        printer.__color = False

    compareOptions = {}
    for item in ["adcPlots", "anyEmap", "printEmap"]:
        compareOptions[item] = getattr(options, item)

    patternOptions = {"rmRibbon": options.rmRibbon,
                      "nTs": integer(options.nts, "nts"),
                      "pureFibersOnly": not options.patternB,
                      "active": options.patterns,
                      }

    mapOptions = {}
    for key in ["filterEvn", "printEventMap", "identityMap"]:
        mapOptions[key] = getattr(options, key)

    printOptions = {"dump": integer(options.dump, "dump"),
                    "warn": not options.noWarnUnpack,
                    "progress": options.progress,
                    "crateslots": configuration.fedList(options.crateslots),
                    }

    feds1 = configuration.fedList(options.feds1)
    feds2 = configuration.fedList(options.feds2)

    def go():
        analyze.oneRun(file1=options.file1,
                       feds1=feds1,
                       file2=options.file2,
                       feds2=feds2,
                       nEvents=integer(options.nevents, "nevents"),
                       nEventsSkip=integer(options.neventsSkip, "neventsSkip"),
                       patternMode=patternOptions,
                       mapOptions=mapOptions,
                       outputFile=options.outputFile,
                       printOptions=printOptions,
                       compareOptions=compareOptions,
                       unpack=not options.noUnpack,
                       unpackSkipFlavors=configuration.fedList(options.unpackSkipFlavors),
                       )

    if not options.noLoop:
        if options.profile:
            cProfile.run("go()", sort="time")
        else:
            go()

    graphs.makeSummaryPdf(inputFiles=[options.outputFile],
                          feds1=feds1,
                          feds2=feds2,
                          pdf=options.outputFile.replace(".root", ".pdf"),
                          scatter=feds2 and not options.anyEmap,
                          )


if __name__ == "__main__":
    main(opts())
