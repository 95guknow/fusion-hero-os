// Local inference engine for simple queries
// Avoids external LLM calls for trivial requests

#include "../management/monitor.h"
#include <stddef.h>

// Simple pattern matching for local responses
static const char* simple_patterns[] = {
    "cpu", "CPU status: Active cores=",
    "mem", "Memory: ",
    "top", "Processes: ",
    "help", "Available: cpu, mem, top, help",
    "ht", "Hyperthreading: Enabled",
    NULL
};

int local_handle_simple_query(char* output, uint32_t* out_len, const char* prompt) {
    // Check for simple patterns we can handle locally
    for (int i = 0; simple_patterns[i]; i += 2) {
        if (simple_patterns[i][0] == prompt[0]) {
            // Generate local response
            const char* resp = simple_patterns[i + 1];
            while (*resp) {
                *output++ = *resp++;
                (*out_len)++;
            }
            return 1;
        }
    }
    return 0;
}

// Rule-based inference for system queries
int local_inference(const char* prompt, char* response, uint32_t* resp_len) {
    // Handle system monitoring queries locally
    if (prompt[0] == 'c' && prompt[1] == 'p' && prompt[2] == 'u') {
        // CPU stats
        int len = 0;
        len += snprintf(response + len, 128, 
            "CPU Count: %d, Active cores: ", cpu_count);
        for (int i = 0; i < cpu_count && len < 200; i++) {
            if (cpus[i].is_active) {
                len += snprintf(response + len, 128 - len, "%d ", i);
            }
        }
        *resp_len = len;
        return 1;
    }
    
    if (prompt[0] == 'm' && prompt[1] == 'e' && prompt[2] == 'm') {
        // Memory stats
        int len = snprintf(response, 128, 
            "Total: %d MB, Used: %d MB, Free: %d MB",
            (int)(stats.memory_total / (1024 * 1024)),
            (int)(stats.memory_used / (1024 * 1024)),
            (int)((stats.memory_total - stats.memory_used) / (1024 * 1024)));
        *resp_len = len;
        return 1;
    }
    
    return 0;
}