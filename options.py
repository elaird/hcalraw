import argparse


def oparser(file1=True):
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    common = parser.add_argument_group("Misc options")
    if file1:
        common.add_argument("--file1",
                            required=True,
                            help=".root file over which to run")

    common.add_argument("--feds1",
                        default="HCAL",
                        help="FEDs to use in file1, e.g. 1114,1122 (default =%(default)s)")
    common.add_argument("--nevents",
                        dest="nEventsMax",
                        default=0,
                        metavar="N",
                        type=int,
                        help="Stop after N events (including skipped events).")
    common.add_argument("--nevents-skip",
                        dest="nEventsSkip",
                        default=0,
                        metavar="M",
                        type=int,
                        help="Skip the first M events.")
    common.add_argument("--output-file",
                        dest="outputFile",
                        default="output/latest.root",
                        metavar="f",
                        help="Store histograms in this .root file.")
    common.add_argument("--sparse-loop",
                        dest="sparseLoop",
                        default=-1,
                        metavar="S",
                        type=int,
                        help="Loop over only (up to) S events per file.")
    common.add_argument("--profile",
                        default=False,
                        action="store_true",
                        help="Profile this program.")
    common.add_argument("--plugins",
                        metavar="a,b,c,...",
                        default="unpack,histogram",
                        help='''(default =%(default)s)
Comma-separated list of plugins to run on each event.
E.g., --plugins=unpack,histogram will execute first
the function unpack from plugins/unpack.py and
then the function histogram from plugins/histogram.py
''')


    less = parser.add_argument_group("Options to do less work")
    less.add_argument("--no-loop",
                      dest="noLoop",
                      default=False,
                      action="store_true",
                      help="Plot from existing .root file (do not look at data).")
    less.add_argument("--last-n-amcs",
                      dest="lastNAmcs",
                      default=0,
                      metavar="N",
                      type=int,
                      help="Consider only the final N AMCs per FED (0 means all).")
    less.add_argument("--first-n-ts",
                      dest="firstNTs",
                      default=8,
                      metavar="N",
                      type=int,
                      help="Consider only the first N time slices (default is %(default)s).")
    less.add_argument("--fewer-histograms",
                      dest="fewerHistos",
                      default=False,
                      action="store_true",
                      help="Save time by making fewer histograms.")
    less.add_argument("--no-plot",
                      dest="noPlot",
                      default=False,
                      action="store_true",
                      help="Do not make .pdf from .root file")


    printing = parser.add_argument_group("Options for printing to stdout")
    printing.add_argument("--no-color",
                          dest="noColor",
                          default=False,
                          action="store_true",
                          help="disable color in stdout")
    printing.add_argument("--progress",
                          default=False,
                          action="store_true",
                          help="print TTree entry number (when power of 2)")
    printing.add_argument("--no-warn-quality",
                          dest="noWarnQuality",
                          default=False,
                          action="store_true",
                          help="suppress warnings about problems with data quality")
    printing.add_argument("--crateslots",
                          default="",
                          metavar="D",
                          help="list of (100*crate)+slot to dump, e.g. 2911,3201")
    printing.add_argument("--per-ts",
                          dest="perTs",
                          default=False,
                          action="store_true",
                          help="print per-TS error bits and cap ids")
    printing.add_argument("--dump",
                          default=-1,
                          metavar="D",
                          type=int,
                          help='''(default is %(default)s)
-1: only program info, warnings and errors
 0: only summary (no per-event info)
 1: DCC/AMC13 headers
 2: (u)HTR summary info
 3: (u)HTR headers
 4: data (fib=2,14  fibCh=1), formatted compactly
 5: data (fib=all   fibCh=1   OK !LE !CE)
 6: data (fib=all   fibCh=1   OK !LE !CE); TPs (> 0)
 7: data (fib=all   fibCh=1             ); TPs (> 0)
 8: data (                    OK !LE !CE); TPs (> 0)
 9: data (all)                           ; TPs (all)
10: data (                   !OK, LE, CE); TPs (!OK)
11: 64bit words; all data and TPs
12: 64(+16)bit words; all data and TPs
''')


    match = parser.add_argument_group("Options for matching events across files")
    match.add_argument("--file2",
                       default="",
                       help=".root file to compare with file1")
    match.add_argument("--feds2",
                       default="",
                       help="FEDs to use in file2, e.g. 931")
    match.add_argument("--identity-map",
                       dest="identityMap",
                       default=False,
                       action="store_true",
                       help="Force use of identity map.")
    match.add_argument("--print-event-map",
                       dest="printEventMap",
                       default=False,
                       action="store_true",
                       help="Print event map to stdout.")


    matchCh = parser.add_argument_group("Options for matching channels across events")
    matchCh.add_argument("--ignore-ce",
                         dest="ignoreCE",
                         default=False,
                         action="store_true",
                         help="Ignore whether CE is asserted")
    matchCh.add_argument("--utca-bcn-delta",
                         dest="utcaBcnDelta",
                         default=0,
                         metavar="n",
                         type=int,
                         help="Add n BX to uTCA BcN counters (default is %(default)s)")
    matchCh.add_argument("--utca-pipe-sub",
                         dest="utcaPipelineDelta",
                         default=0,
                         metavar="n",
                         type=int,
                         help="Subtract n BX from uTCA pipelines (default is %(default)s)")
    matchCh.add_argument("--any-emap",
                         dest="anyEmap",
                         default=False,
                         action="store_true",
                         help="Brute-force search for matches.")
    matchCh.add_argument("--print-emap",
                         dest="printEmap",
                         default=False,
                         action="store_true",
                         help="Print emap found with --any-emap.")
    matchCh.add_argument("--print-mismatches",
                         dest="printMismatches",
                         default=False,
                         action="store_true",
                         help="Print mismatching ADCs or TPs.")

    return parser
