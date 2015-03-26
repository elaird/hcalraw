CC=g++
CFLAGS=-Wall -Wextra
ROOT=`root-config --cflags --libs`

all: rooter deadbeef badcoffee

rooter: rooter.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

deadbeef: deadbeef.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

badcoffee: badcoffee.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

clean:
	rm -f rooter deadbeef badcoffee
