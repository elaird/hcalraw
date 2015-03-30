####Quick Start
```bash
ssh lxplus.cern.ch
git clone https://github.com/elaird/hcalraw.git
cd hcalraw
source env/lxplus6.sh
cd cpp; make; cd -

# read about usage
./oneRun.py --help

# dump decoded data to stdout
./oneRun.py --file1=data/B904_Integration_000050.root --feds1=702,931 --nevents=1 --dump=4

# compare payloads of different sets of FEDs, within one file
./oneRun.py --file1=$LS1/USC_239097.root --feds1=718,719 --feds2=uHF --match=v2 --dump=0 --output-file=output/239097.root --progress

# compare payloads of different sets of FEDs, across two files
./oneRun.py --file1=data/B904_Integration_000055.root --feds1=702 --file2=data/mol_run55.root --feds2=931 --dump=0 --match=v0 --any-emap
./oneRun.py --file1=data/USC_209150.root --feds1=989 --file2=data/209151.HLTSkim.root --feds2=714,722 --dump=0 --match=v0 --any-emap

# analyze FE pattern runs
# (before HO refibering) ./oneRun.py --file1=$LS1/USC_235576.root --feds1=HCAL --nevents=1 --patterns | ./diff.py data/ref_2014.txt
# (before move to uTCA ) ./oneRun.py --file1=$LS1/USC_236631.root --feds1=HCAL --nevents=1 --patterns | ./diff.py data/ref_vme_G.txt
./oneRun.py --file1=$LS1/USC_239099.root --feds1=HCAL --nevents=1 --patterns | ./diff.py data/ref_vme_G.txt
./oneRun.py --file1=$LS1/USC_239099.root --feds1=uHF  --nevents=1 --patterns | ./diff.py data/ref_utca_G.txt

# analyze global runs
./oneRun.py --file1=$GR2/Cosmics/RAW/v1/000/235/316/00000/9CE27CCC-5EBB-E411-AF2C-02163E0127C8.root --output-file=output/235316.root --feds1=718,719 --feds2=1118  --match=v3 --no-warn-unpack --dump=0 --nevents=10
./oneRun.py --file1=$GR2/Cosmics/RAW/v1/000/239/201/00000/0012EAD3-77D6-E411-8052-02163E01351E.root --output-file=output/239201.root --feds1=718,719 --feds2=uHF  --match=v4 --dump=0 --no-warn-unpack --nevents=10
```

####License
[GPLv3](http://www.gnu.org/licenses/gpl.html)

####Dependencies
* python (2.x, x>=6)
* ROOT (>=5.32)

####Environment (SLC6/AFS)
(use exactly one of these)
* `env/lxplus6.sh` sets up CMSSW and the environment vars LS1,GR2
* `env/slc6-cmssw.sh` sets up a CMSSW environment
* `env/slc6-pypy.sh` sets up pypyROOT (outside of CMSSW)
* `env/slc6-root6.sh` sets up a ROOT 6 environment (outside of CMSSW)

####Files
* `cpp/CDF*.h` are copied from CMSSW (IORawData/HcalTBInputService/src)
* `cpp/FED*` are copied from CMSSW (DataFormats/FEDRawData)
* `cpp/[cdf,cms].h` define helper functions
* `cpp/[mol,deadbeef,badcoffee,rooter].cpp` make .root files from binary event dumps
* `analyze.py` loops over .root file(s) for one run and produces output/Runxxx.root
* `autoBook.py` is copied from github.com/elaird/supy/`__autoBook__.py`
* `compare.py` compares the payloads within two .root files for a given event
* `configuration.py` holds some settings that are used by analyze.py
* `decode.py` interprets a FED's bytes in an event (called by analyze.unpacked)
* `diff.py` compares the decoded output of a FiberID run to data/ref.txt
* `dumps2root2pdf.py` converts binary event dumps to .root files and analyzes them
* `graphs.py` reads in output/Runxxx.root, makes plots, and outputs a .pdf
* `make_fiberid_references.py` produces FiberID reference files from HCAL logical maps
* `oneRun.py` is used to analyze one run (see examples above)
* `options.py` parses command line options for `oneRun.py` or `dumps2root2pdf.py`
* `printRaw.py` dumps to stdout the payload(s) in an event
* `printer.py` contains a utility class for printing messages
* `processUSC.py` loops over available USC local runs and processes them
* `test_transformation.py` tests `configuration.transformed()`
* `utils.py` contains helper functions
