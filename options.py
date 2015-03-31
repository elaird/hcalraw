import optparse
import sys


def opts(alsoArgs=False):
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
                      dest="nEvents",
                      default=None,
                      metavar="N",
                      type="int",
                      help="Stop after N events (including skipped events).")
    common.add_option("--nevents-skip",
                      dest="nEventsSkip",
                      default=0,
                      metavar="M",
                      type="int",
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
                        type="int",
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
                        dest="nTs",
                        default=10,
                        metavar="N",
                        type="int",
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

    if alsoArgs and not args:
        parser.print_help()
        sys.exit(1)

    return options, args
