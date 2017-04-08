#!/bin/bash

./look.py $1 --quiet --plugins=patterns ${@:2} | ./diff.py data/ref_2017.txt
