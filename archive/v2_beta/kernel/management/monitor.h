#ifndef MONITOR_H
#define MONITOR_H

#include <stdint.h>

// System Monitoring Structure
typedef struct {
    uint64_t cpu_usage[smp_cpu_count];      // Per-CPU usage %
    uint64_t cpu_temperature;               // Temperature in millidegrees
    uint64_t memory_used;
    uint64_t memory_total;
    uint64_t processes_running;
    uint64_t interrupts_total;
    uint64_t context_switches;
} system_stats_t;

// Monitoring Functions
void monitor_init(void);
void monitor_update_stats(void);
void monitor_draw_cpu_panel(void);
void monitor_draw_memory_panel(void);
void monitor_draw_process_list(void);
void monitor_check_ht_performance(void);

// GUI Components
typedef struct {
    uint16_t x, y;
    uint16_t width, height;
    uint8_t color;
    char title[32];
} panel_t;

#endif
