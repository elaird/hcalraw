source /afs/.cern.ch/sw/lcg/external/pypy/x86_64-slc5/setup-cint.sh
mkdir bin >& /dev/null
ln -s `which pypy-cint` bin/python >& /dev/null
export PATH=bin/:${PATH}