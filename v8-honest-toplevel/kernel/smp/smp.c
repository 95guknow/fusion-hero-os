#include "smp.h"
#include "../include/stdint.h"

static cpu_info_t cpus[256];
static uint32_t cpu_count = 0;

// I/O APIC base address
static uint32_t* io_apic_base = (uint32_t*)0xFEC00000;

// Local APIC base address
static uint32_t* lapic_base = (uint32_t*)0xFEE00000;

void smp_init(void) {
    detect_cpu_topology();
    
    // Initialize BSP APIC
    init_local_apic(cpus[0].apic_id);
    
    // Initialize I/O APIC for interrupt distribution
    init_io_apic();
    
    // Set up LAPIC timer for each core
    for (uint32_t i = 0; i < cpu_count; i++) {
        if (cpus[i].is_active) {
            // Configure timer interrupt per core
            lapic_base[0x320 / 4] = 0x00000000; // Timer LVT - masked
        }
    }
}

void detect_cpu_topology(void) {
    uint32_t eax, ebx, ecx, edx;
    
    // Get hyperthreading support
    eax = 1;
    __asm__ volatile ("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx) : "a"(eax));
    
    int ht_support = (edx & (1 << 28)) != 0; // HTT bit
    
    // Get core count
    eax = 0x80000008;
    __asm__ volatile ("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx) : "a"(eax));
    
    int cores = (eax & 0xff) + 1;
    int logical_per_core = (ebx & 0xff) + 1;
    
    // Store topology info
    cpus[0].logical_per_core = (uint8_t)logical_per_core;
    cpus[0].core_id = 0;
    cpus[0].thread_id = 0;
    cpus[0].is_active = 1;
    
    // Detect other cores via LAPIC IDs
    // This would normally parse ACPI MADT table
    cpu_count = cores * logical_per_core;
    
    // For now, assume we have detected all cores
    for (uint32_t i = 1; i < cpu_count && i < 256; i++) {
        cpus[i].apic_id = i;
        cpus[i].core_id = i / logical_per_core;
        cpus[i].thread_id = i % logical_per_core;
        cpus[i].logical_per_core = (uint8_t)logical_per_core;
        cpus[i].is_active = 0; // APs not yet started
    }
}

void init_local_apic(uint32_t apic_id) {
    // Enable xAPIC
    uint64_t apic_base;
    __asm__ volatile ("rdmsr" : "=a"(apic_base) : "c"(0x1b));
    __asm__ volatile ("wrmsr" :: "a"(apic_base | 0x800), "d"(apic_base >> 32), "c"(0x1b));
    
    // Mask all interrupts initially
    lapic_base[0x320 / 4] = 0x00000000; // LVT Timer - masked
    lapic_base[0x330 / 4] = 0x00000000; // LVT LINT0 - masked
    lapic_base[0x340 / 4] = 0x00000000; // LVT LINT1 - masked
    lapic_base[0x350 / 4] = 0x00000000; // LVT Performance Counter - masked
    lapic_base[0x360 / 4] = 0x00000000; // LVT LINT1 - masked
}

void init_io_apic(void) {
    // I/O APIC initialization
    // Set up ID register
    io_apic_base[0x00 / 4] = 0x00000000;
    
    // Set up I/O APIC version
    io_apic_base[0x01 / 4] = 0x00000000;
    
    // Configure I/O APIC redirection table
    // This maps IRQ 0-23 to vectors 32-55
    for (int i = 0; i < 24; i++) {
        io_apic_base[0x10 + i * 2] = 0x00000000; // Clear low
        io_apic_base[0x10 + i * 2 + 1] = 0x00000000; // Clear high (IRQ disabled)
    }
}

void send_ipi(uint32_t apic_id, uint8_t vector) {
    // Send IPI to specific CPU via LAPIC ICR
    // ICR low: vector in bits 7:0, delivery mode in bits 10:8
    lapic_base[0x300 / 4] = (0x0 << 8) | vector; // Fixed delivery mode
    // ICR high: destination APIC ID
    lapic_base[0x310 / 4] = apic_id << 24;
}
