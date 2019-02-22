#!/usr/bin/env python

import collections, optparse, os
import graphs, oneRun, printer, utils
from options import oparser
from configuration import sw


def this_machine(run):
    out = []
    for filename in sw.files_this_machine(run):
        if os.path.exists(filename):
            out.append(filename)
    return out


def local_eos(run, check=False):
    out = []
    for filename in sw.files_eos_local(run):
        shortName = filename[filename.find("/store"):]
        if check and utils.commandOutputFull("eos stat %s" % shortName)["returncode"]:
            continue
        out.append(filename)
    return out


def global_eos(run, hhmmMin=None, quiet=False):
    month_num = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr":  4, "May":  5, "Jun":  6,
                 "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

    for d in sw.dirs_global(run):
        shortName = d[d.find(".ch/") + 4:]
        # stat = utils.commandOutputFull("eos stat %s" % shortName)
        # if stat["returncode"]:
        #     continue

        ll = utils.commandOutputFull("eos ls -l %s" % d)
        listings = [x for x in ll["stdout"].split("\n") if x]

        coords = []
        for listing in listings:
            fields = listing.split()
            month, day, hhmm, fileName = fields[-4:]
            hh, mm = hhmm.split(":")
            coords.append((month_num[month], int(day), int(hh), int(mm), fileName))

        coords.sort()
        if hhmmMin:
            mmMin = hhmmMin % 100
            hhMin = hhmmMin // 100
            coords = [x for x in coords if hhMin < x[2] or (hhMin == x[2] and mmMin <= x[3])]
            if not quiet:
                for c in coords:
                    print(c)

        files = []
        for c in coords:
            files.append(d + c[-1])
        return files


def report(fileNames):
    pieces = [f.split("/") for f in fileNames]
    bases = set(["/".join(piece[:-1]) for piece in pieces])
    assert len(bases) == 1, bases
    if len(fileNames) == 1:
        printer.info("found matching file %s" % fileNames[0])
    else:
        printer.info("found %4d file(s) in %s/" % (len(fileNames), "/".join(bases)))


def override(options, run, nRuns):
    options.outputFile = "output/%d.root" % run
    if not options.nEventsMax:
        options.nEventsMax = 4

    if (not options.quiet) and (nRuns == 1):
        options.progress = True
        if options.dump == -1:
            options.dump = 0


def opts():
    parser = oparser(arg="RUN_NUMBER [RUN_NUMBER2 ...]")

    look = optparse.OptionGroup(parser, "Options solely for use with look.py")
    look.add_option("--quiet",
                    dest="quiet",
                    default=False,
                    action="store_true",
                    help="Print less to stdout")
    look.add_option("--hhmm",
                    dest="hhmm",
                    default=None,
                    type="int",
                    help="minimum hhmm")
    parser.add_option_group(look)

    options, args = parser.parse_args()

    runs = []
    for arg in args:
        try:
            runs.append(int(arg))
        except ValueError:
            printer.warning("Could not convert '%s' to an integer." % arg)

    if not runs:
        printer.error("Please provide a run number as the argument.")

    return options, runs


def search(run):
    for search_func in [this_machine, local_eos, global_eos]:
        files = search_func(run)
        # options.file1 = find_gr(run, grDir, options.hhmm, quiet)
        if files:
            return files


def pruned(files):
    pieces = collections.defaultdict(list)
    for f in files:
        filename = f.split("/")[-1]
        pieces[filename].append(f)

    out = []
    for filename, bases in sorted(pieces.items()):
        out.append(sorted(bases)[0])

    return out


def go(options, run, nRuns):
    override(options, run, nRuns)

    files = ["dummy"] if options.noLoop else search(run)

    if not files:
        printer.warning("Did not find a matching file for run %d." % run)
        return 1, None, None

    files = pruned(files)

    nFiles = len(files)
    if 2 <= nFiles:
        options.file1 = ",".join(files)
        if options.hhmm is None:
            options.sparseLoop = max(1, options.nEventsMax // nFiles)
        else:
            options.sparseLoop = -1
    else:
        options.file1 = files[0]
        sw.set_default_feds1(options)

    if not options.quiet:
        report(files)

    return oneRun.main(options)


def main():
    options, runs = opts()

    roots = []
    feds1s = []
    feds2s = []
    for run in runs:
        retCode, feds1, feds2 = go(options, run, len(runs))
        if not retCode:
            roots.append(options.outputFile)
            feds1s.append(feds1)
            feds2s.append(feds2)

    if 2 <= len(roots):
        for i, stem in enumerate(graphs.all_pages):
            graphs.makeSummaryPdfMulti(inputFiles=roots,
                                       feds1s=feds1s,
                                       feds2s=feds2s,
                                       pdf="output/%d_%s.pdf" % (1 + i, stem),
                                       pages=[stem])


if __name__ == "__main__":
    main()
