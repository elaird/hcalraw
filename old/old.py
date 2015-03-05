#!/usr/bin/env python


def opts():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("--run", dest="run", default=None, metavar="N", help="run number")
    options, args = parser.parse_args()

    if not options.run:
        parser.print_help()
        exit()
    try:
        int(options.run)
    except ValueError:
        print "ERROR: run number '%s' cannot be converted to an int." % options.run
        exit()
    return options


options = opts()
if not all([x[0] == "_" or x in ["x", "opts", "options"] for x in dir()]):
    print dir()
    print "Please put imports after this block, to prevent PyROOT from stealing '--help'."


dir = "/afs/cern.ch/user/e/elaird/work/public/d1_utca/"
run = int(options.run)

import os
if run == 209151:
    os.system(" ".join(["./oneRun.py",
                        "--file1=%s/usc/USC_209150.root" % dir,
                        "--feds1=989",
                        "--file2=%s/castor/209151.HLTSkim.root" % dir,
                        "--feds2=714,722",
                        ]))

if run == 211155:
    os.system(" ".join(["./oneRun.py",
                        "--file1=%s/usc/USC_211155.root" % dir,
                        "--feds1=989",
                        "--file2=%s/usc/USC_211154.root" % dir,
                        "--feds2=714,722",
                        ]))

if run == 211428:
    os.system(" ".join(["./oneRun.py",
                        "--file1=%s/usc/USC_211428.root" % dir,
                        "--feds1=989",
                        "--file2=%s/usc/USC_211427.root" % dir,
                        "--feds2=714,722",
                        ]))

if run >= 212928:
    os.system(" ".join(["./oneRun.py",
                        "--file1=%s/USC_%d.root" % (dir, run),
                        "--feds1=725",
                        ]))

if run <= 200000:  # including None
    fileName = dir+"/904/B904_Integration_%06d.root" % run
    os.system(" ".join(["./oneRun.py",
                        "--file1=%s" % fileName,
                        "--feds1=931",
                        #"--file2=%s" % fileName,
                        #"--feds2=702",
                        ]))
