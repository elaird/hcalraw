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
ssh lxplus.cern.ch #or some other host

#if you have git and a github account:
git clone git@github.com:elaird/hcal.git

#if you have only git:
git clone git://github.com/elaird/hcal.git

#if you have neither:
wget foobar.zip

cd hcal/utca
source env.sh #see below
./analyze.py

---------
| Files |
---------
env.sh sets up a CMSSW environment (needed to analyze CMS data);
       it requires AFS; it is not needed to analyze HCAL test-stand data.

cpp/CDF*.h are copied from CMSSW (IORawData/HcalTBInputService/src)
cpp/cdf.cxx defines a helper class for reading data from HCAL local DAQ
cpp/cms.cxx defines a helper class for reading data from the CMS DAQ

autoBook.py is copied from github.com/elaird/supy/__autoBook__.py
analyze.py loops over .root file(s) for one run and produces output/Runxxx.root
cmsswUnpack.py is not needed, but could be executed with cmsRun
multiRun.py calls analyze.py (once per run) and produces summary.pdf
compare.py compares the payloads within two .root files for a given event
decode.py interprets a FED's bytes in an event (called by analyze.unpacked)
graphs.py reads in output/Runxxx.root, makes plots, and outputs summary.pdf
printRaw.py dumps to stdout the payload(s) in an event
utils.py contains helper functions

---------
| To do |
---------
(documentation)
readme: versions, wget, rst

(technical)
TChain support
TTree cache
unpack by words in CMS format
improve storage structure
clean up unpacking loop
PEP 8

(analysis)
HLT path filter in analyze.py
electronics map
