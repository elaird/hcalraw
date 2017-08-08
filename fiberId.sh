#!/bin/bash

./look.py --quiet --plugins=unpack,patterns --nevents=1 $* | ./diff.py data/ref_2017.txt
