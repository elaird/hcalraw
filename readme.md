####Quick Start
```bash
ssh lxplus.cern.ch
git clone https://github.com/elaird/hcalraw.git
cd hcalraw
source env/lxplus6.sh
cd cpp; make -j 5; cd -


# analyze a global or local run
./look.py 235316 --hf --no-warn-unpack --no-warn-quality
./look.py 239342 --hf --utca-pipeline-delta=4
./look.py 239895 --hf --hhmm=2212 --nevents=20
./look.py 246908 --hf --nevents=100
./look.py 251244 --hf --nevents=300

./look.py 268148

# analyze several global runs
cat gr_list.txt | ./multi.py --nevents=100
cat gr_list.txt | ./dqReport.py


# analyze AMC13/DCC2 monitor buffer dumps
# HF (USC FEDs):
./dumps2root2pdf-HF.py data/239713_*.dat
# from a single AMC13:
export FEDID=999
cat foo.dat | cpp/badcoffee ${FEDID}
./oneRun.py --file1=badcoffee${FEDID}.root --feds1=${FEDID} --progress


# compare payloads of different sets of FEDs, within one file
./look.py 239480 --hf
./oneRun.py --file1=$LS1/USC_239480.root --feds1=718,719 --feds2=uHF \
--dump=0 --output-file=output/239480.root --progress --utca-bcn-delta=-131


# dump decoded data to stdout
./oneRun.py --file1=data/B904_Integration_000055.root --feds1=702,931 \
--nevents=1 --dump=4


# compare payloads of different sets of FEDs, across two files
./oneRun.py --file1=data/B904_Integration_000055.root --feds1=702 \
--file2=data/mol_run55.root --feds2=931 --dump=0 --any-emap \
--no-warn-quality --ok-errf=0,1 --utca-bcn-delta=-119

./oneRun.py --file1=$USC/USC_211154.root --feds1=714,722 --nevents=51 --progress \
--file2=$USC/USC_211155.root --feds2=989 --utca-bcn-delta=-119 --any-emap --dump=0


# analyze FE pattern runs
# (before HO refibering) ./oneRun.py --file1=$LS1/USC_235576.root --feds1=HCAL --plugins=patterns | ./diff.py data/ref_2014.txt
# (before move to uTCA ) ./oneRun.py --file1=$LS1/USC_236631.root --feds1=HCAL --plugins=patterns | ./diff.py data/ref_vme_G.txt
./fiberId.sh 260773
./fiberId.sh 270688

# read about usage
./oneRun.py --help
```

####License
[GPLv3](http://www.gnu.org/licenses/gpl.html)


####Design Goals
* unpack both VME and uTCA data
* digest global, local, or monitor buffer data without configuration
* compare payloads across two .root files containing unsorted events
* enable evaluation of board performance in only one page of plots
* provide flexibility in analysis
* not require CMSSW


####Dependencies
* python (2.x, x>=6)
* [ROOT](https://root.cern.ch/) (>=5.32)


####Environment (SLC6/AFS)
(use exactly one of these)
* `env/lxplus6.sh` sets up CMSSW, EOS, and the environment vars LS1,USC
* `env/slc6-pypy.sh` sets up pypyROOT (outside of CMSSW)
* `env/slc6-root6.sh` sets up a ROOT 6 environment (outside of CMSSW)


####Files
* `cpp/CDF*.h` are copied from CMSSW (IORawData/HcalTBInputService/src)
* `cpp/FED*` are copied from CMSSW (DataFormats/FEDRawData)
* `cpp/[cdf,cms].h` define helper functions
* `cpp/[mol,deadbeef,badcoffee,rooter].cpp` make .root files from binary event dumps
* `analyze.py` loops over .root file(s) for one run and produces output/Runxxx.root
* `autoBook.py` is copied from github.com/elaird/supy/`__autoBook__.py`
* `configuration/` holds some settings that are used by analyze.py
* `decode.py` interprets a FED's bytes in an event (called by analyze.unpacked)
* `diff.py` compares the decoded output of a FiberID run to data/ref.txt
* `dumps2root2pdf.py` converts binary event dumps to .root files and analyzes them
* `graphs.py` reads in output/Runxxx.root, makes plots, and outputs a .pdf
* `look.py` will find a file in EOS (or locally) for a given run and loop over it
* `make_fiberid_references.py` produces FiberID reference files from HCAL logical maps
* `oneRun.py` is used to analyze one run (see examples above)
* `options.py` parses command line options for `oneRun.py` or `dumps2root2pdf.py`
* `printer.py` contains a utility class for printing messages
* `processUSC.py` loops over available USC local runs and processes them
* `test_transformation.py` tests `configuration.hw.transformed*`
* `utils.py` contains helper functions

####plugins/
* `compare.py` compares the payloads within two .root files for a given event
* `patterns.py` interprets the raw data as front-end patterns
* `printraw.py` dumps to stdout the payload(s) in an event
