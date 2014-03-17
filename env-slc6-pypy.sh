# http://root.cern.ch/drupal/content/pypyroot
source /afs/.cern.ch/sw/lcg/external/pypy/x86_64-slc6/setup-pypyroot.sh
mkdir bin >& /dev/null
rm bin/python >& /dev/null
ln -s `which pypyroot` bin/python >& /dev/null
export PATH=bin/:${PATH}
