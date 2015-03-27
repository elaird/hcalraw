#define START_FLAG 0  // only for MOL
#define START_MASK 0  // only for MOL
#define SAVE_HEADER 0

#define WORD uint64_t
#define NHEADER 2
#define MAGIC 0xbadc0ffeebadcafe
#define MASK  0xffffffffffffffff
#define TAG "badcoffee"

#include "mb_loop.cpp"
