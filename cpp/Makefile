CC=g++
CFLAGS=-Wall -Wextra
ROOT=`root-config --cflags` -L`root-config --libdir` -lCore -lTree -lRIO
SO=-shared -fPIC
HS=CDFChunk.h CDFEventInfo.h CDFRunInfo.h

TMP=tmp.cpp
RV=$(shell root-config --version | cut -c 1)
ifeq ($(RV), 6)
	RC=rootcling -f $(TMP) $(HS) LinkDef.h
endif
ifeq ($(RV), 5)
	RC=rootcint -f $(TMP) -c $(HS) CDFROOTLinkDef.h
endif

all: mol deadbeef badcoffee cdf.so

mol: mol.cpp rooter.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

deadbeef: deadbeef.cpp rooter.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

badcoffee: badcoffee.cpp rooter.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

cdf.so: $(HS) cdf.cxx
	$(RC)
	$(CC) $(CFLAGS) $(SO) $(ROOT) $(TMP) cdf.cxx -o $@

clean:
	rm -f mol deadbeef badcoffee *.pcm *.d *.so $(TMP)
