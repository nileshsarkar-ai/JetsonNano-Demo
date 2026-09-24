#ifndef JETSON_DEMO_GCC8_NEON_H
#define JETSON_DEMO_GCC8_NEON_H

/* GCC 8's AArch64 arm_neon.h lacks the x4 byte-load intrinsics used by
 * the pinned ggml. Four ordinary 16-byte loads preserve lane order and
 * signedness. Keep upstream sources untouched so pinned checkout checks work.
 * The force switch is only for compiling the regression on newer compilers.
 */
#if defined(__aarch64__) && ((defined(__GNUC__) && !defined(__clang__) && __GNUC__ == 8) || defined(JETSON_TEST_GCC8_NEON))
#include <arm_neon.h>
static inline int8x16x4_t jetson_vld1q_s8_x4(const int8_t *p) {
    int8x16x4_t r;
    r.val[0] = vld1q_s8(p);
    r.val[1] = vld1q_s8(p + 16);
    r.val[2] = vld1q_s8(p + 32);
    r.val[3] = vld1q_s8(p + 48);
    return r;
}
static inline uint8x16x4_t jetson_vld1q_u8_x4(const uint8_t *p) {
    uint8x16x4_t r;
    r.val[0] = vld1q_u8(p);
    r.val[1] = vld1q_u8(p + 16);
    r.val[2] = vld1q_u8(p + 32);
    r.val[3] = vld1q_u8(p + 48);
    return r;
}
#undef vld1q_s8_x4
#define vld1q_s8_x4 jetson_vld1q_s8_x4
#undef vld1q_u8_x4
#define vld1q_u8_x4 jetson_vld1q_u8_x4
#endif
#endif
