#!/usr/bin/env python

import os

os.system("nsls /castor/cern.ch/cms/store/hidata/HIRun2013A/HcalNZS/RAW/v1/000/210/ > runs")

lines = [line[:-1] for line in open("runs")]

for last3 in reversed(lines) :
    print last3
    os.system("nsls -l /castor/cern.ch/cms/store/hidata/HIRun2013A/HcalNZS/RAW/v1/000/210/"+last3)
f.close()
