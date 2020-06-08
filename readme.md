#### Quick Start
```bash
ssh lxplus.cern.ch
git clone https://github.com/elaird/hcalraw.git
cd hcalraw
cd cpp; make -j 5; cd -

./look.py 284928
./look.py 289555 --nevents=1 --dump=8
./look.py 294542 --feds1=1115 --nevents=1000
```

#### More Examples
```bash
# analyze AMC13/DCC2 monitor buffer dumps
# HF (USC FEDs):
./dumps2root2pdf-HF.py data/239713_*.dat
# from a single AMC13:
export FEDID=999
cat foo.dat | cpp/badcoffee ${FEDID}
./oneRun.py --file1=badcoffee${FEDID}.root --feds1=${FEDID} --progress

# compare payloads of different sets of FEDs, within one file
./look.py 239480 --feds1=718,719 --feds2=HF --dump=0 --utca-bcn-delta=-131 --no-warn-quality --plugins=histogram,compare

# dump decoded data to stdout
./look.py 55 --feds1=702,931 --nevents=1 --dump=4

# compare payloads of different sets of FEDs, across two files
./oneRun.py --file1=data/B904_Integration_000055.root --feds1=702 \
--file2=data/mol_run55.root --feds2=931 --dump=0 --any-emap \
--no-warn-quality --ignore-ce --utca-bcn-delta=-119

export EOS=root://eoscms.cern.ch//store/group/dpg_hcal/comm_hcal/archival/20160914_USC_Run1_runs133054-220908; \
./oneRun.py --nevents=51 --progress --utca-bcn-delta=-119 --any-emap --no-warn-quality --dump=0 \
--file1=${EOS}/USC_211154.root --feds1=714,722 \
--file2=${EOS}/USC_211155.root --feds2=989

# analyze FE pattern runs
# (before HO refibering) ./look.py 235576 --feds1=HO  --plugins=unpack,patterns --dump=0 | ./diff.py data/ref_2014.txt
# (before move to uTCA ) ./look.py 236631 --feds1=7xy --plugins=unpack,patterns --dump=0 | ./diff.py data/ref_vme_G.txt
# ./look.py --quiet --progress --plugins=unpack,patterns,bitwalk --nevents=8000 --feds1=1115 --last-n-amcs=2 300703
./look.py 260773 --feds1=HBEF --plugins=unpack,patterns --dump=0 | ./diff.py data/ref_utca_G.txt
./look.py 270688 --feds1=HBEF --plugins=unpack,patterns --dump=0 | ./diff.py data/ref_utca_G.txt
./fiberId.sh 288606

# read about usage
./oneRun.py --help
```

#### License
[GPLv3](http://www.gnu.org/licenses/gpl.html)


#### Design Goals
* unpack both VME and uTCA data
* digest global, local, or monitor buffer data without configuration
* compare payloads across two .root files containing unsorted events
* enable evaluation of board performance in only one page of plots
* provide flexibility in analysis
* not require CMSSW


#### Dependencies
* python (>=2.7)
* [ROOT](https://root.cern.ch/) (>=5.32)


#### Environment
(use exactly one of these)
* `env/cc7-cvmfs.sh` sets up a ROOT 6 environment on cc7
* `env/lxplus6.sh` sets up CMSSW and EOS
* `env/slc6-pypy.sh` sets up pypyROOT (outside of CMSSW)


#### Files
* `cpp/CDF*.h` are copied from CMSSW (IORawData/HcalTBInputService/src)
* `cpp/FED*` are copied from CMSSW (DataFormats/FEDRawData)
* `cpp/[cdf,cms].h` define helper functions
* `cpp/[mol,deadbeef,badcoffee,rooter].cpp` make .root files from binary event dumps
* `analyze.py` loops over .root file(s) for one run and produces output/Runxxx.root
* `autoBook.py` is copied from github.com/elaird/supy/`__autoBook__.py`
* `configuration/` holds some settings used by `analyze.py`, `plugins/`, etc.
* `decode.py` interprets a FED's bytes in an event (called by raw.unpacked)
* `diff.py` compares the decoded output of a FiberID run to data/ref.txt
* `dumps2root2pdf-HF.py` converts binary event dumps to .root files and analyzes them
* `graphs.py` reads in output/Runxxx.root, makes plots, and outputs a .pdf
* `look.py` will find a files in EOS (or locally) for given runs and loop over them
* `make_fiberid_references.py` produces FiberID reference files from HCAL logical maps
* `oneRun.py` is used to analyze one run (see examples above)
* `options.py` parses command line options for `oneRun.py`, `look.py`, or `dumps2root2pdf-HF.py`
* `printer.py` contains utility functions for printing messages
* `processUSC.py` loops over available USC local runs and processes them
* `raw.py` reads and unpacks raw data
* `test_transformation.py` tests `configuration.hw.transformed*` and `utils.shortList`
* `utils.py` contains helper functions

#### plugins/
* `compare.py` compares the payloads within two .root files for a given event
* `histogram.py` books and fills many per-FED and per-event histograms
* `patterns.py` interprets the raw data as front-end patterns
* `printraw.py` dumps to stdout the payload(s) in an event
