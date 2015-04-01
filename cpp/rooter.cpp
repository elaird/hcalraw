/* NOTE!
   The function below requires some #defines
   See e.g. badcoffee.cpp
*/

#include "TFile.h"
#include "TTree.h"
#include "TROOT.h"
#include <iostream>
#include <stdint.h>


int NDataInBlock(uint64_t buf){
  int nData = (buf>>56);
  nData += (buf>>40) & 0x300;
  return nData;
}


int read_word(WORD& buf) {
  return fread(&buf, sizeof(buf), 1, stdin);
}


void loop(TTree& tree, std::vector<WORD>& vec, bool debug=false) {
  int iWordInBlock = 0;
  int nWordsInBlock = 0;

  WORD buf;
  int success = read_word(buf);

  while (success) {
    if (debug) std::cout << iWordInBlock;

    if ((buf & MASK) == MAGIC) {
      if((iWordInBlock - NHEADER != nWordsInBlock) && nWordsInBlock)
        std::cerr << "Warning: found magic number in data with iWord = " << iWordInBlock << " nWordsInBlock = " << nWordsInBlock << std::endl;
      else if (iWordInBlock){  // found new block
	if (debug) std::cout << " filling/clearing" << std::endl;

	iWordInBlock = 0;

	if(START_FLAG) {  // MOL
	  nWordsInBlock = NDataInBlock(buf);
	  if ((buf & START_MASK) == START_FLAG && vec.size()) {  // new fragment
	    tree.Fill();
	    vec.clear();
	  }
	}
        else {  // not MOL
	  tree.Fill();
	  vec.clear();
	}

      }  // end new block
    }  // end magic word

    if((!START_FLAG) && (iWordInBlock == 1)) {  // not MOL
      nWordsInBlock = buf;
    }

    if(SAVE_HEADER || (NHEADER <= iWordInBlock)){
      vec.push_back(buf);
      if(debug) std::cout << " pushing_back " << std::hex << buf << std::dec << std::endl;
    }
    else if(debug) std::cout << std::endl;

    iWordInBlock++;
    success = read_word(buf);
  }
}

int main(int argc, char* argv[]) {
  if (argc != 2){
    std::cout << "Usage: cat a.dat | " << argv[0] << " FEDnumber" << std::endl;
    return 1;
  }

  std::vector<WORD> vec;
  vec.reserve(1 << 13);
  vec.clear();

  gROOT->ProcessLine("#include <vector>\n #pragma link C++ class vector<uint32_t>+; #pragma link C++ class vector<uint64_t>+;");
  TFile a(Form("%s%s.root", TAG, argv[1]), "RECREATE");
  TTree tree(TAG,"");
  tree.Branch(Form("%s", argv[1]), &vec);

  loop(tree, vec);

  tree.Fill();
  tree.Write();
  a.Close();
  return 0;
}
