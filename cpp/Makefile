CC=g++
CFLAGS=-Wall -Wextra
ROOT=`root-config --cflags` -L`root-config --libdir` -lCore -lTree -lRIO
SO=-shared -fPIC
HS=CDFChunk.h CDFEventInfo.h CDFRunInfo.h cdf.h FEDRawData.h cms.h
CXXS=FEDRawData.cc

TMP=tmp.cpp
RV=$(shell root-config --version | cut -c 1)
ifeq ($(RV), 6)
	RC=rootcling -f $(TMP) $(HS) CDFROOTLinkDef.h
endif
ifeq ($(RV), 5)
	RC=rootcint -f $(TMP) -c $(HS) CDFROOTLinkDef.h
endif

all: mol deadbeef badcoffee formats.so

mol: mol.cpp rooter.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

deadbeef: deadbeef.cpp rooter.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

badcoffee: badcoffee.cpp rooter.cpp
	$(CC) $(CFLAGS) $(ROOT) $< -o $@

formats.so: $(HS) $(CXXS)
	$(RC)
	$(CC) $(CFLAGS) $(SO) $(ROOT) $(CXXS) $(TMP) -o $@

clean:
	rm -f mol deadbeef badcoffee *.pcm *.d *.so $(TMP)
