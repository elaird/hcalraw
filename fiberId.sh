#!/bin/bash

./look.py $1 --quiet --plugins=patterns --nevents=1 ${@:2} | ./diff.py data/ref_2017.txt
