#include "DataFormats/FEDRawData/interface/FEDRawData.h"

//expose std::vector
class FEDRawData2 : public FEDRawData {
public:
  FEDRawData2(const FEDRawData& in) {data_ = in.data_;}
  std::vector<unsigned char>& vectorChar() {return data_;}
  //std::vector<ULong64_t> vectorLong() {return std::vector<ULong64_t> (data(), data() + size()/8);}//re-interpret in CDFChunk format, i.e. vector of ULong64_t
};

//linkdef for reading Tree
#include "IORawData/HcalTBInputService/src/CDFROOTLinkDef.h"

//expose std::vector
class CDFChunk2 : public CDFChunk {
public:
  CDFChunk2(const CDFChunk& in) {fChunkLength = in.fChunkLength; fChunk = in.fChunk;}
  Int_t length() {return fChunkLength;}
  //http://www.cplusplus.com/reference/vector/vector/vector/
  std::vector<ULong64_t> chunk() {return std::vector<ULong64_t> (fChunk, fChunk + fChunkLength);}
  ClassDef(CDFChunk2, 1);
};
