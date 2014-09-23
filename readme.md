####License
[GPLv3](http://www.gnu.org/licenses/gpl.html)

####Dependencies
* python (2.x, x>=6)
* ROOT (>=5.32)
* CMSSW is required to analyze files written by the CMS central DAQ; whereas
* CMSSW is *not* required to analyze data from HCAL local runs

####Quick Start
```bash
ssh lxplus.cern.ch
git clone https://github.com/elaird/hcalraw.git
cd hcalraw
source env/slc6-cmssw.sh
./oneRun.py --help
./oneRun.py --file1=data/B904_Integration_000050.root --feds1=702,931
./oneRun.py --file1=data/B904_Integration_000050.root --feds1=702,931 --nevents=1 --dump=4
./oneRun.py --file1=data/B904_Integration_000050.root --feds1=702 --feds2=931 --shiftFibCh2
./oneRun.py --file1=data/B904_Integration_000055.root --feds1=702 --file2=data/mol_run55.root --feds2=931
./oneRun.py --file1=data/B904_Integration_000067.root --feds1=702 --patterns --nevents=1
./oneRun.py --file1=data/USC_214784.root --feds1=HCAL --patterns --nevents=1
./oneRun.py --file1=data/USC_217924.root --feds1=HCAL --patterns --nevents=1 | ./diff.py
```

####Environment
######SLC6/AFS
* `env/slc6-cmssw.sh` sets up a CMSSW environment
* `env/slc6-pypy.sh` sets up pypyROOT (outside of CMSSW)

######SLC5/AFS
* `env/slc5-cmssw.sh` sets up a CMSSW environment
* `env/slc5-cpython.sh` sets up pyROOT (outside of CMSSW)

####Files
* `cpp/CDF*.h` are copied from CMSSW (IORawData/HcalTBInputService/src)
* `cpp/cdf.cxx` defines a helper class for reading data from HCAL local DAQ
* `cpp/cms.cxx` defines a helper class for reading data from the CMS DAQ
* `autoBook.py` is copied from github.com/elaird/supy/`__autoBook__.py`
* `analyze.py` loops over .root file(s) for one run and produces output/Runxxx.root
* `configuration.py` holds some settings that are used by analyze.py
* `cmsswUnpack.py` is not needed, but could be executed with cmsRun
* `diff.py` compares the decoded output of a fiberID run to data/ref.txt
* `multiRun.py` is broken
* `oneRun.py` is used to analyze one run (see examples above)
* `compare.py` compares the payloads within two .root files for a given event
* `decode.py` interprets a FED's bytes in an event (called by analyze.unpacked)
* `graphs.py` reads in output/Runxxx.root, makes plots, and outputs summary.pdf
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
