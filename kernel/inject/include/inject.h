/* Fusion Hero OS — Kernel Injection ABI (Assembly-first, max injectability)
 *
 * Geltung: Spezifikation + Host-simulierbar · Bare-metal freestanding optional
 * Security: capability-gated · no arbitrary foreign-process injection
 */
#ifndef FHOS_KERNEL_INJECT_H
#define FHOS_KERNEL_INJECT_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define FHOS_INJECT_MAGIC        0x46484F53494E4A00ULL /* "FHOSINJ\0" truncated */
#define FHOS_INJECT_SLOTS        256
#define FHOS_INJECT_NAME_MAX     32

/* Capability bits (MasterSeed-aligned gates) */
#define FHOS_CAP_NONE            0u
#define FHOS_CAP_READ            (1u << 0)
#define FHOS_CAP_HOOK            (1u << 1)
#define FHOS_CAP_SWAP            (1u << 2)
#define FHOS_CAP_ISR             (1u << 3)
#define FHOS_CAP_QUANTUM         (1u << 4)
#define FHOS_CAP_PRIV            (1u << 7)  /* requires integrity attestation */

/* Slot flags */
#define FHOS_SLOT_EMPTY          0u
#define FHOS_SLOT_ACTIVE         (1u << 0)
#define FHOS_SLOT_HOT            (1u << 1)  /* hot-swappable */
#define FHOS_SLOT_ASM            (1u << 2)  /* entry is assembly trampoline */
#define FHOS_SLOT_HOST           (1u << 3)  /* host-simulated (Windows) */

typedef uint64_t (*fhos_inject_fn)(uint64_t a0, uint64_t a1, uint64_t a2, uint64_t a3);

typedef struct fhos_inject_slot {
    uint32_t flags;
    uint32_t required_caps;
    uint32_t quantum_id;       /* Q0=0 … Q12=12, 0xFFFFFFFF = freeform */
    uint32_t generation;       /* bumps on every swap */
    fhos_inject_fn entry;      /* assembly trampoline or C/Rust ABI */
    char name[FHOS_INJECT_NAME_MAX];
} fhos_inject_slot_t;

typedef struct fhos_inject_table {
    uint64_t magic;
    uint32_t n_slots;
    uint32_t active_count;
    uint64_t epoch;
    fhos_inject_slot_t slots[FHOS_INJECT_SLOTS];
} fhos_inject_table_t;

/* Assembly-exported (see inject_table.s / inject_dispatch.s) */
extern fhos_inject_table_t fhos_inject_table;
void fhos_inject_init(void);
int  fhos_inject_register(uint32_t slot, const char *name, uint32_t quantum_id,
                          uint32_t caps, uint32_t flags, fhos_inject_fn fn);
int  fhos_inject_swap(uint32_t slot, fhos_inject_fn fn, uint32_t holder_caps);
uint64_t fhos_inject_call(uint32_t slot, uint64_t a0, uint64_t a1,
                          uint64_t a2, uint64_t a3, uint32_t holder_caps);
int  fhos_inject_clear(uint32_t slot, uint32_t holder_caps);

#ifdef __cplusplus
}
#endif
#endif /* FHOS_KERNEL_INJECT_H */
