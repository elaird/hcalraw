import optparse


def oparser(arg=""):
    if arg:
        parser = optparse.OptionParser(usage="usage: %prog [options] " + arg)
    else:
        parser = optparse.OptionParser()

    reqd = optparse.OptionGroup(parser, "REQUIRED")
    reqd.add_option("--file1",
                    dest="file1",
                    default="",
                    help=".root file over which to run")
    reqd.add_option("--feds1",
                    dest="feds1",
                    default="HCAL",
                    help="FEDs to use in file1, e.g. 714,722 (default =HCAL)")
    parser.add_option_group(reqd)

    common = optparse.OptionGroup(parser, "Misc options")
    common.add_option("--nevents",
                      dest="nEventsMax",
                      default=0,
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
    common.add_option("--sparse-loop",
                      dest="sparseLoop",
                      default=-1,
                      metavar="S",
                      type="int",
                      help="Loop over only (up to) S events per file.")
    common.add_option("--profile",
                      dest="profile",
                      default=False,
                      action="store_true",
                      help="Profile this program.")

    plugins = ["Comma-separated list of plugins to run on each event.",
               "E.g., --plugins=unpack,histogram will execute first",
               "the function unpack from plugins/unpack.py and",
               "then the function histogram from plugins/histogram.py"
              ]
    common.add_option("--plugins",
                      dest="plugins",
                      type="str",
                      metavar="unpack,histogram,...",
                      default="unpack,histogram",
                      help=" ".join([l.ljust(60) for l in plugins]))
    parser.add_option_group(common)

    less = optparse.OptionGroup(parser, "Options to do less work")
    less.add_option("--no-loop",
                    dest="noLoop",
                    default=False,
                    action="store_true",
                    help="Plot from existing .root file (do not look at data).")
    less.add_option("--last-n-amcs",
                    dest="lastNAmcs",
                    default=0,
                    metavar="N",
                    type="int",
                    help="Consider only the final N AMCs per FED (0 means all).")
    less.add_option("--first-n-ts",
                    dest="firstNTs",
                    default=10,
                    metavar="N",
                    type="int",
                    help="Consider only the first N time slices (default is 10).")
    less.add_option("--fewer-histograms",
                    dest="fewerHistos",
                    default=False,
                    action="store_true",
                    help="Save time by making fewer histograms.")
    less.add_option("--no-plot",
                    dest="noPlot",
                    default=False,
                    action="store_true",
                    help="Do not make .pdf from .root file")
    parser.add_option_group(less)

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
    printing.add_option("--no-warn-quality",
                        dest="noWarnQuality",
                        default=False,
                        action="store_true",
                        help="suppress warnings about problems with data quality")
    printing.add_option("--crateslots",
                        dest="crateslots",
                        default="",
                        metavar="D",
                        help="list of (100*crate)+slot to dump, e.g. 917,2911")
    printing.add_option("--per-ts",
                        dest="perTs",
                        default=False,
                        action="store_true",
                        help="print per-TS error bits and cap ids")

    dump = ["dump level (default is -1)",
            "-1: only program info, warnings and errors",
            "0:  only summary (no per-event info)",
            "1:  DCC/AMC13 headers",
            "2:  (u)HTR summary info",
            "3:  (u)HTR headers",
            "4:  data (fib=2,14  fibCh=1), formatted compactly",
            "5:  data (fib=all   fibCh=1   OK !LE !CE)",
            "6:  data (fib=all   fibCh=1   OK !LE !CE); TPs (> 0)",
            "7:  data (fib=all   fibCh=1             ); TPs (> 0)",
            "8:  data (                    OK !LE !CE); TPs (> 0)",
            "9:  data (all)                           ; TPs (all)",
            "10: data(                    !OK, LE, CE); TPs (!OK)",
            "11: 64bit words; all data and TPs",
            "12: 64(+16)bit words; all data and TPs",
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
    matchCh.add_option("--ignore-ce",
                       dest="ignoreCE",
                       default=False,
                       action="store_true",
                       help="Ignore whether CE is asserted")
    matchCh.add_option("--utca-bcn-delta",
                       dest="utcaBcnDelta",
                       default=0,
                       metavar="n",
                       type="int",
                       help="Add n BX to uTCA BcN counters (default is 0)")
    matchCh.add_option("--utca-pipe-sub",
                       dest="utcaPipelineDelta",
                       default=0,
                       metavar="n",
                       type="int",
                       help="Subtract n BX from uTCA pipelines (default is 0)")
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
    matchCh.add_option("--print-mismatches",
                       dest="printMismatches",
                       default=False,
                       action="store_true",
                       help="Print mismatching ADCs or TPs.")
    parser.add_option_group(matchCh)

    return parser
