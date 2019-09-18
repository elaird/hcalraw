#!/bin/bash

./look.py --quiet --dump=0 --plugins=unpack,patterns --nevents=1 $* | ./diff.py data/ref_2020.txt
