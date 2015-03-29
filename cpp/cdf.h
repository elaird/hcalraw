#include "CDFChunk.h"

std::vector<ULong64_t> CDFChunk2(CDFChunk& in) {
  ULong64_t* data = in.getData();
  return std::vector<ULong64_t> (data, data + in.getDataLength());
}
