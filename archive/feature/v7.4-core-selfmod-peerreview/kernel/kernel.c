#include "../include/stdint.h"
#include "../smp/smp.h"

// Kernel entry point - called from boot.s
void kernel_main(uint64_t multiboot_info) {
    // Initialize SMP with hyperthreading support
    smp_init();
    
    // Initialize console output
    console_init();
    
    // Print CPU information
    console_print("Fusion Hero OS - SMP Kernel\n");
    console_print("Detected cores with hyperthreading: ");
    
    uint32_t esp;
    __asm__ volatile ("movl %%esp, %0" : "=r"(esp));
    
    // Start multitasking - each core can run tasks
    smp_start_scheduler();
    
    // Main kernel loop
    while (1) {
        __asm__ volatile ("hlt");
        
        // Handle inter-processor interrupts for HT cores
        // Each logical processor (SMT sibling) can handle tasks independently
        for (uint32_t i = 0; i < 256; i++) {
            if (cpus[i].is_active && cpus[i].logical_per_core > 1) {
                // Hyperthreading: cores have multiple logical processors
                // Load balance between siblings
                smp_balance_load(i);
            }
        }
    }
}

// Console output for debugging
void console_init(void) {
    // Initialize VGA text mode
    uint16_t* vga = (uint16_t*)0xB8000;
    for (int i = 0; i < 80 * 25; i++) {
        vga[i] = 0x0720; // Space with light gray on black
    }
}

void console_print(const char* str) {
    static uint16_t* vga = (uint16_t*)0xB8000;
    static uint32_t col = 0;
    
    while (*str) {
        if (*str == '\n') {
            col += 80;
        } else {
            vga[col] = (uint8_t)*str | 0x0700;
            col++;
        }
        str++;
    }
}

// Placeholder for SMP load balancing
void smp_balance_load(uint32_t cpu_id) {
    // In a real implementation, this would:
    // 1. Check sibling threads' load via shared memory
    // 2. Migrate tasks between HT siblings if needed
    // 3. Consider cache locality for optimal performance
}

// Placeholder for SMP scheduler
void smp_start_scheduler(void) {
    // Enable LAPIC timer interrupts
    uint32_t* lapic = (uint32_t*)0xFEE00000;
    lapic[0x320 / 4] = 0x000020000; // Timer LVT, unmasked, one-shot
    lapic[0x3E0 / 4] = 1000000;     // Timer initial count
    lapic[0x320 / 4] = 0x000021000; // Timer LVT, unmasked, periodic
}
