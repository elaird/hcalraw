//linkdef for reading Tree
#include "CDFROOTLinkDef.h"

//expose std::vector
class CDFChunk2 : public CDFChunk {
public:
  CDFChunk2(const CDFChunk& in) {
    fChunkLength = in.fChunkLength;
    fChunk = in.fChunk;
  }
  Int_t length() {return fChunkLength;}
  std::vector<ULong64_t> chunk() {
    return std::vector<ULong64_t> (fChunk, fChunk + fChunkLength);
  }
  ClassDef(CDFChunk2, 1);
};
