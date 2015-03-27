CC=g++
CFLAGS=-Wall -Wextra
ROOT=`root-config --cflags` -L`root-config --libdir` -lCore -lTree -lRIO

all: mol deadbeef badcoffee

mol: mol.cpp rooter.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

deadbeef: deadbeef.cpp rooter.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

badcoffee: badcoffee.cpp rooter.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

clean:
	rm -f mol deadbeef badcoffee
