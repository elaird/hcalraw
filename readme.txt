-----------
| License |
-----------
GPLv3 (http://www.gnu.org/licenses/gpl.html)

----------------
| Dependencies |
----------------
python (2.x, x>=6) and ROOT (>=y) are required.
When analyzing files written by the CMS DAQ, CMSSW (>=z) is also required.

---------------
| Quick Start |
---------------
ssh lxplus5.cern.ch #or some other host

#if you have only git:
git clone https://github.com/elaird/hcalraw.git

#if not:
wget https://github.com/elaird/hcalraw/archive/master.zip

cd hcalraw
source env-cmssw.sh #see below
./oneRun.py --file=data/B904_Integration_000050.root
./oneRun.py --file=data/B904_Integration_000067.root --patterns

---------
| Files |
---------
env-cmssw.sh sets up a CMSSW environment (needed to analyze CMS data);
       it requires AFS; it is not needed to analyze HCAL test-stand
       data.

cpp/CDF*.h are copied from CMSSW (IORawData/HcalTBInputService/src)
cpp/cdf.cxx defines a helper class for reading data from HCAL local DAQ
cpp/cms.cxx defines a helper class for reading data from the CMS DAQ

autoBook.py is copied from github.com/elaird/supy/__autoBook__.py
analyze.py loops over .root file(s) for one run and produces output/Runxxx.root
configuration.py holds some settings that are used by analyze.py
cmsswUnpack.py is not needed, but could be executed with cmsRun
multiRun.py calls analyze.py (once per run) and produces summary.pdf
oneRun.py calls analyze.py and has various hard-coded paths, fedIds, etc.
compare.py compares the payloads within two .root files for a given event
decode.py interprets a FED's bytes in an event (called by analyze.unpacked)
graphs.py reads in output/Runxxx.root, makes plots, and outputs summary.pdf
printRaw.py dumps to stdout the payload(s) in an event
utils.py contains helper functions

---------
| To do |
---------
(technical)
readme: versions, rst
TChain support
TTree cache
unpack by words in CMS format
improve storage structure
clean up unpacking loop

(analysis)
HLT path filter in analyze.py
electronics map
