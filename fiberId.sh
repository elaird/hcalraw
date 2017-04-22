#!/bin/bash

./look.py --quiet --plugins=patterns --nevents=1 $* | ./diff.py data/ref_2017.txt
