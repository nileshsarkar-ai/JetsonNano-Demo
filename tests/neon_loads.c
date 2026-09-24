/* Regression for every lane, signed bytes, and an unaligned input address. */
#include <stdint.h>
#include <assert.h>
#include "../scripts/compat/gcc8_neon.h"
int main(void) {
    int8_t s[65], out_s[64];
    uint8_t u[65], out_u[64];
    for (int i=0; i<65; ++i) { s[i]=(int8_t)(i*5-128); u[i]=(uint8_t)(255-i*3); }
    int8x16x4_t a = vld1q_s8_x4(s+1);
    uint8x16x4_t b = vld1q_u8_x4(u+1);
    for (int i=0; i<4; ++i) { vst1q_s8(out_s+i*16,a.val[i]); vst1q_u8(out_u+i*16,b.val[i]); }
    for (int i=0; i<64; ++i) { assert(out_s[i]==s[i+1]); assert(out_u[i]==u[i+1]); }
    return 0;
}
