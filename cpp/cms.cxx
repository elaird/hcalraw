#include "FEDRawData.cc"
#include <stdint.h>

const std::vector<unsigned char> FEDRawDataChars(const FEDRawData& in) {
  const unsigned char * data = in.data();
  return std::vector<unsigned char> (data, data + in.size());
}

const std::vector<uint64_t> FEDRawDataWords(const FEDRawData& in) {
  if (in.size() & 0x7) {
    std::cerr << "ERROR: payload truncated" << std::endl;
  }
  int s = in.size()/8;
  uint64_t * data = (uint64_t *) in.data();
  return std::vector<uint64_t> (data, data + s);
}
