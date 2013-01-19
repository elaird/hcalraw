ssh lxplus.cern.ch

#either
git clone git@github.com:elaird/hcal.git #if you have a github account
#or
git clone git://github.com/elaird/hcal.git #if not

cd hcal/utca
source env.sh
./analyze.py
