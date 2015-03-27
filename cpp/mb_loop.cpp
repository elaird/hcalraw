// SEE WARNING!!

#include "TFile.h"
#include "TTree.h"
#include "TROOT.h"
#include <iostream>
#include <stdint.h>


int main(int argc, char* argv[]) {
  gROOT->ProcessLine("#include <vector>; #pragma link C++ class vector<uint32_t>+; #pragma link C++ class vector<uint64_t>+;");
  
  if (argc != 2){
    std::cerr << "Usage: cat a.dat | " << argv[0] << " FEDnumber" << std::endl;
    return 1;
  }

  bool debug = false;

  TFile a(Form("%s%s.root", TAG, argv[1]), "RECREATE");
  TTree tree(TAG,"");
  

  int iWordInBlock = 0;
  std::vector<WORD> vec(1 << 13);
  vec.clear();

  tree.Branch(Form("bc%s", argv[1]), &vec);

  WORD buf;
  int nWordsInBlock = 0;
  int success = fread(&buf, sizeof(buf), 1, stdin);  // read a word!

  while (success) {
    if (debug) std::cout << iWordInBlock;

    if (buf == MAGIC) {
      if((iWordInBlock - NHEADER != nWordsInBlock) && nWordsInBlock)
        std::cout << "Warning::Found magic number in data with iWords = " << iWordInBlock << " nWordsInBlock = " << nWordsInBlock << std::endl;
      else if (iWordInBlock){
        tree.Fill();  //Save

        //Clear Counters
        iWordInBlock = 1;
	vec.clear();
	if (debug) std::cout << " filling/clearing" << std::endl;

        //Get nWords
        if(fread(&buf, sizeof(buf), 1, stdin)) nWordsInBlock = buf; //read next word which contains nWords
      }
    }

    if(NHEADER <= iWordInBlock){  //choose to store the block header
      if(debug) std::cout << " pushing_back " << std::hex << buf << std::dec << std::endl;
      vec.push_back(buf);  // store the word into vector
    }
    else if(debug) std::cout << std::endl;

    iWordInBlock++;
    success = fread(&buf, sizeof(buf), 1, stdin);  // read another word!
  }

  tree.Fill();
  tree.Write();
  a.Close();

  return 0;
}
