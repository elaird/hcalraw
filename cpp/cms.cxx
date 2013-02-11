#include "DataFormats/FEDRawData/interface/FEDRawData.h"

//expose std::vector
class FEDRawData2 : public FEDRawData {
public:
  FEDRawData2(const FEDRawData& in) {data_ = in.data_;}
  std::vector<unsigned char>& vectorChar() {return data_;}
};
