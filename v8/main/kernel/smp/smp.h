#ifndef SMP_H
#define SMP_H

#include <stdint.h>

// CPU Information Structure
typedef struct {
    uint32_t apic_id;
    uint32_t core_id;
    uint32_t thread_id;
    uint8_t logical_per_core;
    uint8_t is_active;
} cpu_info_t;

// SMP Functions
void smp_init(void);
void detect_cpu_topology(void);
void init_local_apic(uint32_t apic_id);
void init_io_apic(void);
void send_ipi(uint32_t apic_id, uint8_t vector);

// Interrupt handlers for SMP
extern void isr0();
extern void isr32();  // Local APIC timer
extern void isr33();  // IPI handler
extern void isr34();  // IPI handler

#endif
