#ifndef FEDRawData_FEDRawDataCollection_h
#define FEDRawData_FEDRawDataCollection_h

#include "FEDRawData.h"
#include <vector>

class FEDRawDataCollection {
 public:
  FEDRawDataCollection(): data_(1) {}
  virtual ~FEDRawDataCollection() {}
  const FEDRawData&  FEDData(int fedid) const {return data_[fedid];}
  FEDRawData&        FEDData(int fedid) {return data_[fedid];}
  FEDRawDataCollection(const FEDRawDataCollection &in) : data_(in.data_) {}
  void swap(FEDRawDataCollection & other) {data_.swap(other.data_);}
 private:
  std::vector<FEDRawData> data_;
  ClassDef(FEDRawDataCollection, 1)
};

inline
void swap(FEDRawDataCollection & a, FEDRawDataCollection & b) {
  a.swap(b);
}

#endif
