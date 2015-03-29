// https://twiki.cern.ch/twiki/bin/viewauth/CMS/CMD_FEROL_DOC

#define START_FLAG (1L<<39)  // initial block: bit 31 --> 39 (endian flip), as well as zeroes in 42..32
#define START_MASK 0x80ffff0000L
#define SAVE_HEADER 1

#define WORD uint64_t
#define NHEADER 2
#define MAGIC 0x5a47  // GZ
#define MASK  0xffff
#define TAG "mol"

#include "rooter.cpp"
