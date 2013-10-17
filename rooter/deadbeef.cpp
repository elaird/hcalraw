/* Rooter: stores MOL output from stdin in a ROOT TTree of 64-bit values
 * 
 * Syntax: cat input.dat | rooter output.root
 */
#include "TFile.h"
#include "TTree.h"
#include "TROOT.h"
#include <iostream>
#include <stdint.h>

#define DB 0xdeadbeef // deadbeef format start header
#define SaveVecBranch 1 //Switch to choose between storing vector or array 
#define SaveHeader 0//Switch to choose if we want to store the header word into the root file


uint32_t ByteSwap32(uint32_t buf){
    uint32_t SwapResult = (buf>>24);
    SwapResult += (buf >> 8) & 0xff00;
    SwapResult += (buf << 8) & 0xff0000;
    SwapResult += (buf << 24) & 0xff000000;
    return SwapResult;
}

int main(int argc, char* argv[]) {
  gROOT->ProcessLine("#include <vector>; #pragma link C++ class vector<uint32_t>+;"); //Load dictionary for vector<uint64_t>
  char* rootfile;
  if (argc == 1) strcpy(rootfile, "deadbeef.root");
  else rootfile = argv[1];
  TFile a(rootfile, "RECREATE");
  TTree tree("deadbeeftree","");
  
  const int MAX_WORDS = 100000;

  int iWordInBlock = 0;
  uint32_t blob[MAX_WORDS];
  std::vector<uint32_t> vec(MAX_WORDS);
  vec.clear();
  if(SaveVecBranch) tree.Branch(Form("db928"), &vec);
  else{
    tree.Branch("nWord32",&iWordInBlock,"nWord32/I");
    tree.Branch("words",blob,"words[nWord32]/l");
  }
  uint32_t buf;
  int nWordsInBlock = 0;
  int success = fread(&buf,sizeof(buf),1,stdin); // read a word!
  while (success) {
    if (buf == DB) { // if found deadbeef
      if((iWordInBlock-2 != nWordsInBlock) && nWordsInBlock)
        std::cout<<std::dec<<"Warning::Found deadbeef in data with iWords = "<<iWordInBlock<<" nWordsInBlock = "<<nWordsInBlock<<std::endl;
      else if (iWordInBlock){
        //Save
        tree.Fill();
        //Clear Counters
        iWordInBlock = 1;
	    vec.clear();
    
        //Get nWords
        if(fread(&buf,sizeof(buf),1,stdin)) nWordsInBlock = buf; //read next word which contains nWords
      }
    }
    
    if(iWordInBlock >= 2){//choose to store the block header
      blob[iWordInBlock-2] = buf; // store the read word
      vec.push_back(buf); // store the word into vector
    }    
    iWordInBlock++;
    success = fread(&buf,sizeof(buf),1,stdin); // read another word!
  }
  tree.Fill();
  tree.Write();
  a.Close();
  return 0;
}
