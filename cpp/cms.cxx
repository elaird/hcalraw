#include "FEDRawData.cc"

const std::vector<unsigned char> FEDRawData2(const FEDRawData& in) {
  const unsigned char * data = in.data();
  return std::vector<unsigned char> (data, data + in.size());
}
