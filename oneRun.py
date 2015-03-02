#!/usr/bin/env python


def opts():
    import optparse
    import sys
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
                      help="stop after N events (including skipped events)")
    common.add_option("--nevents-skip",
                      dest="neventsSkip",
                      default=0,
                      metavar="M",
                      help="skip the first M events")
    common.add_option("--output-file",
                      dest="outputFile",
                      default="output/latest.root",
                      metavar="f",
                      help="store histograms in this .root file.")
    common.add_option("--profile",
                      dest="profile",
                      default=False,
                      action="store_true",
                      help="profile the run")
    common.add_option("--utca-bcn-delta",
                     dest="utcaBcnDelta",
                     default=-119,
                     metavar="N",
                     help="Add this to uTCA BcN (and OrN).  Default is -119.")
    common.add_option("--adc-plots",
                      dest="adcPlots",
                      default=False,
                      action="store_true",
                      help="Histogram ADC values.")
    common.add_option("--no-unpack",
                      dest="noUnpack",
                      default=False,
                      action="store_true",
                      help="loop over raw data, but do not unpack it")
    parser.add_option_group(common)

    printing = optparse.OptionGroup(parser, "Options for printing to stdout")
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
    printing.add_option("--crateslots",
                        dest="crateslots",
                        default=None,
                        metavar="D",
                        help="Whitelist of (100*crate)+slot to dump.")
    uscSummer2014 = "917,918,2911,2912"
    printing.add_option("--usc-summer2014",
                        dest="uscSummer2014",
                        default=False,
                        action="store_true",
                        help="--crateslots=%s" % uscSummer2014)
    bat904Crates2014 = "2,3012"
    printing.add_option("--bat904-2014",
                        dest="bat904Crates2014",
                        default=False,
                        action="store_true",
                        help="--crateslots=%s" % bat904Crates2014)
    printing.add_option("--no-warn-skip16",
                        dest="noWarnSkip16",
                        default=False,
                        action="store_true",
                        help="disable warning when unpacker skips 16-bit words")
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
    match.add_option("--use-evn",
                     dest="useEvn",
                     default=False,
                     action="store_true",
                     help="Require matching EvN.")
    match.add_option("--filter-evn",
                     dest="filterEvn",
                     default=False,
                     action="store_true",
                     help="Consider only EvN with (EvN & 0x1fff) == 0.")
    match.add_option("--orn-tolerance",
                     dest="ornTolerance",
                     default=0,
                     metavar="N",
                     help="Consider |OrN1 - OrN2| <= N a match (default is 0).")
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
    matchCh.add_option("--shiftFibCh2",
                     dest="shiftFibCh2",
                     default=False,
                     action="store_true",
                     help="Shift fibCh=2 by 1 TS to compensate for uHTR f/w bug.")
    matchCh.add_option("--skipErrF",
                     dest="skipErrF",
                     default="1,3",
                     metavar="s",
                     help="Skip channels with these ErrF values (default is 1,3).")
    matchCh.add_option("--skipAllZero",
                     dest="skipAllZero",
                     default=False,
                     action="store_true",
                     help="Skip channels with all QIE samples = 0.")

    matchCh.add_option("--adc-vs-adc",
                       dest="adcVsAdc",
                       default=False,
                       action="store_true",
                       help="Make a scatter plot of uTCA vs. VME ADC values.")
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
    patterns.add_option("--compressed",
                        dest="compressed",
                        default=False,
                        action="store_true",
                        help="Handle lack of capids by doing (code>>1)&0x3f + 32.")
    patterns.add_option("--no-asciify",
                        dest="noAsciify",
                        default=False,
                        action="store_true",
                        help="Do not convert hex codes to ASCII.")
    patterns.add_option("--no-reg-match",
                        dest="noRegMatch",
                        default=False,
                        action="store_true",
                        help="Print full pattern, even if it matches regexp.")
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
    if not all([options.file1, options.feds1]):
        parser.print_help()
        sys.exit(1)
    if not options.outputFile.endswith(".root"):
        sys.exit("--output-file must end with .root (%s)" % options.outputFile)
    if options.feds2 and not options.file2:
        print "Using --file1 also for --file2; also using identity map"
        options.file2 = options.file1
        options.identityMap = True

    if all([options.uscSummer2014, options.bat904Crates2014]):
        sys.exit("Use at most one of --usc-summer2014, --bat904-2014")

    if options.uscSummer2014:
        if options.crateslots is not None:
            print "--usc-summer2014: forcing --crateslots=%s" % uscSummer2014
        options.crateslots = uscSummer2014

    if options.bat904Crates2014:
        if options.crateslots is not None:
            print "--bat904-2014: forcing --crateslots=%s" % bat904Crates2014
        options.crateslots = bat904Crates2014

    return options


def integer(value="", tag=""):
    if value == '':
        return None

    try:
        return int(value)
    except ValueError:
        sys.exit("%s '%s' cannot be converted to an int." % (tag, value))


def fedList(s=""):
    d = configuration.fedMap()
    if not s:
        return []
    if s in d:
        return d[s]

    out = [int(x) for x in s.split(",")]
    return out


def checkModules():
    import types
    names = []
    for key, value in globals().iteritems():
        if isinstance(value, types.ModuleType):
            names.append(key)
    if names != ["__builtins__"]:
        print names
        print "Please put imports after this block, to prevent PyROOT from stealing '--help'."


if __name__ == "__main__":
    options = opts()
    checkModules()

    import analyze
    import configuration
    import printer
    import sys
    import cProfile

    configuration.__shiftFibCh2 = options.shiftFibCh2
    configuration.__utcaBcnDelta = integer(options.utcaBcnDelta)
    configuration.__compressedPatterns = options.compressed
    configuration.__asciifyPatterns = not options.noAsciify
    configuration.__regMatchPatterns = not options.noRegMatch

    if options.noColor:
        printer.__color = False

    compareOptions = {"skipErrF": fedList(options.skipErrF)}
    for item in ["adcPlots", "skipAllZero", "adcVsAdc"]:
        compareOptions[item] = getattr(options, item)

    patternOptions = {"rmRibbon": options.rmRibbon,
                      "nTs": integer(options.nts, "nts"),
                      "pureFibersOnly": not options.patternB,
                      "compressed": options.compressed,
                      "active": options.patterns,
                      }

    mapOptions = {"ornTolerance": integer(options.ornTolerance, "orn-tolerance")}
    for key in ["useEvn", "filterEvn", "printEventMap", "identityMap"]:
        mapOptions[key] = getattr(options, key)

    printOptions = {"dump": integer(options.dump, "dump"),
                    "warnSkip16": not options.noWarnSkip16,
                    "progress": options.progress,
                    "crateslots": fedList(options.crateslots),
                    }
    def go():
        analyze.oneRun(file1=options.file1,
                       feds1=fedList(options.feds1),
                       file2=options.file2,
                       feds2=fedList(options.feds2),
                       nEvents=integer(options.nevents, "nevents"),
                       nEventsSkip=integer(options.neventsSkip, "neventsSkip"),
                       patternMode=patternOptions,
                       mapOptions=mapOptions,
                       outputFile=options.outputFile,
                       printOptions=printOptions,
                       compareOptions=compareOptions,
                       unpack=not options.noUnpack,
                       )

    if options.profile:
        cProfile.run("go()", sort="time")
    else:
        go()


    feds = fedList(options.feds1) + fedList(options.feds2)
    if len(feds) <= 3:
        import graphs
        graphs.makeSummaryPdf(inputFiles=[options.outputFile],
                              feds=feds,
                              pdf=options.outputFile.replace(".root", ".pdf"),
                              )

    if options.adcVsAdc:
        import adc_vs_adc
        for exclude in [False, True]:
            adc_vs_adc.go(fileName=options.outputFile, exclude=exclude)
