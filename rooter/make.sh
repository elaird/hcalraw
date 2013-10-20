#!/bin/sh

g++ rooter.cpp -I `root-config --incdir --libs` -o rooter
g++ deadbeef.cpp -I `root-config --incdir --libs` -o deadbeef