CC=g++
CFLAGS=-Wall -Wextra
ROOT=`root-config --cflags` -L`root-config --libdir` -lCore -lTree -lRIO

all: rooter mol deadbeef badcoffee

rooter: rooter.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

mol: mol.cpp mb_loop.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

deadbeef: deadbeef.cpp mb_loop.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

badcoffee: badcoffee.cpp mb_loop.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

clean:
	rm -f rooter mol deadbeef badcoffee
