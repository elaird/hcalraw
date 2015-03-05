####Quick Start
```bash
ssh lxplus.cern.ch
git clone https://github.com/elaird/hcalraw.git
cd hcalraw
source env/lxplus6.sh

# read about usage
./oneRun.py --help

# dump decoded data to stdout
./oneRun.py --file1=data/B904_Integration_000050.root --feds1=702,931 --nevents=1 --dump=4

# compare payloads of different sets of FEDs, within one file
./oneRun.py --file1=$LS1/USC_234155.root --feds1=HF --feds2=uHF --progress --nevents=20 --match=v1 --dump=0 --adc-vs-adc
./oneRun.py --file1=$LS1/USC_235728.root --feds1=718,719 --feds2=1118 --progress --nevents=20 --match=v1 --dump=0 --adc-vs-adc

# compare payloads of different sets of FEDs, across two files
./oneRun.py --file1=data/B904_Integration_000055.root --feds1=702 --file2=data/mol_run55.root --feds2=931 --dump=0 --match=v0 --skipErrF=3

# analyze FE pattern runs
./oneRun.py --file1=$LS1/USC_231834.root --feds1=uHF  --nevents=1 --patterns --compressed | ./diff.py --ref=data/ref_utca_G.txt
./oneRun.py --file1=$LS1/USC_235576.root --feds1=HCAL --nevents=1 --patterns --compressed | ./diff.py --ref=data/ref_2014.txt
./oneRun.py --file1=$LS1/USC_236631.root --feds1=HCAL --nevents=1 --patterns --compressed | ./diff.py --ref=data/ref_vme_G.txt

# analyze global runs
./oneRun.py --file1=root://eoscms.cern.ch//store/data/Commissioning2015/Cosmics/RAW/v1/000/234/193/00000/FEAD7C2C-4CB4-E411-9791-02163E011890.root --feds1=718,719 --feds2=1118 --progress
```

####License
[GPLv3](http://www.gnu.org/licenses/gpl.html)

####Dependencies
* python (2.x, x>=6)
* ROOT (>=5.32)
* CMSSW is required to analyze files written by the CMS central DAQ; whereas
* CMSSW is *not* required to analyze data from HCAL local runs

####Environment (SLC6/AFS)
(use exactly one of these)
* `env/lxplus6.sh` sets up CMSSW and EOS
* `env/slc6-cmssw.sh` sets up a CMSSW environment
* `env/slc6-pypy.sh` sets up pypyROOT (outside of CMSSW)
* `env/slc6-root6.sh` sets up a ROOT 6 environment (outside of CMSSW)

####Files
* `cpp/CDF*.h` are copied from CMSSW (IORawData/HcalTBInputService/src)
* `cpp/cdf.cxx` defines a helper class for reading data from HCAL local DAQ
* `cpp/cms.cxx` defines a helper class for reading data from the CMS DAQ
* `adc_vs_adc.py` if `--adc-vs-adc` is passed to `oneRun.py`, makes plots from output/Runxxx.root
* `analyze.py` loops over .root file(s) for one run and produces output/Runxxx.root
* `autoBook.py` is copied from github.com/elaird/supy/`__autoBook__.py`
* `compare.py` compares the payloads within two .root files for a given event
* `configuration.py` holds some settings that are used by analyze.py
* `decode.py` interprets a FED's bytes in an event (called by analyze.unpacked)
* `diff.py` compares the decoded output of a fiberID run to data/ref.txt
* `graphs.py` reads in output/Runxxx.root, makes plots, and outputs summary.pdf
* `make_fiberid_references.py` produces FiberID reference files from HCAL logical maps
* `oneRun.py` is used to analyze one run (see examples above)
* `printRaw.py` dumps to stdout the payload(s) in an event
* `printer.py` contains a utility class for printing messages
* `processUSC.py` loops over available USC local runs and processes them
* `utils.py` contains helper functions

####To do
* TChain support
* TTree cache
* unpack by words in CMS format
* improve storage structures
* HLT path filter in analyze.py
* electronics map
