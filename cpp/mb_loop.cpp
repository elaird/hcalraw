/* NOTE!
   The function below requires some #defines
   See e.g. badcoffee.cpp
*/

#include "TFile.h"
#include "TTree.h"
#include "TROOT.h"
#include <iostream>
#include <stdint.h>

#define SAVE_HEADER 0  // switch to store the header word into the root file


int NDataInBlock(uint64_t buf){
  int nData = (buf>>56);
  nData += (buf>>40) & 0x300;
  return nData;
}


int read_word(WORD& buf) {
  return fread(&buf, sizeof(buf), 1, stdin);
}


int main(int argc, char* argv[]) {
  gROOT->ProcessLine("#include <vector>; #pragma link C++ class vector<uint32_t>+; #pragma link C++ class vector<uint64_t>+;");
  
  if (argc != 2){
    std::cerr << "Usage: cat a.dat | " << argv[0] << " FEDnumber" << std::endl;
    return 1;
  }

  bool debug = false;

  TFile a(Form("%s%s.root", TAG, argv[1]), "RECREATE");
  TTree tree(TAG,"");
  

  std::vector<WORD> vec(1 << 13);
  vec.clear();

  tree.Branch(Form("%s", argv[1]), &vec);

  int iWordInBlock = 0;
  int nWordsInBlock = 0;

  WORD buf;
  int success = read_word(buf);

  while (success) {
    if (debug) std::cout << iWordInBlock;

    if ((buf & MASK) == MAGIC) {
      if((iWordInBlock - NHEADER != nWordsInBlock) && nWordsInBlock)
        std::cerr << "Warning: found magic number in data with iWords = " << iWordInBlock << " nWordsInBlock = " << nWordsInBlock << std::endl;
      else if (iWordInBlock){
	if (debug) std::cout << " filling/clearing" << std::endl;

        tree.Fill();

        iWordInBlock = 1;
	vec.clear();
        //Get nWords
        if(read_word(buf)) {
	  nWordsInBlock = buf; //read next word which contains nWords
	}
      }
    }

    if(SAVE_HEADER || (NHEADER <= iWordInBlock)){
      if(debug) std::cout << " pushing_back " << std::hex << buf << std::dec << std::endl;
      vec.push_back(buf);  // store the word into vector
    }
    else if(debug) std::cout << std::endl;

    iWordInBlock++;
    success = read_word(buf);
  }

  tree.Fill();
  tree.Write();
  a.Close();

  return 0;
}
