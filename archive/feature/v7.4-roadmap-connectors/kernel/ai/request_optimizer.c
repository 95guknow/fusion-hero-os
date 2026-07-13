#include "request_optimizer.h"
#include "local_inference.h"
#include <stddef.h>

#define CACHE_SIZE 256
#define BATCH_SIZE 8

static char cache_prompts[CACHE_SIZE][128];
static char cache_responses[CACHE_SIZE][256];
static uint32_t cache_hashes[CACHE_SIZE];
static int cache_valid[CACHE_SIZE];
static uint32_t cache_count = 0;
static optimized_request_t pending_batch[BATCH_SIZE];
static uint32_t batch_count = 0;

void req_optimizer_init(void) {
    for (int i = 0; i < CACHE_SIZE; i++) {
        cache_valid[i] = 0;
        cache_hashes[i] = 0;
    }
    batch_count = 0;
}

uint32_t req_compute_hash(const char* prompt) {
    uint32_t hash = 5381;
    while (*prompt) {
        hash = ((hash << 5) + hash) + *prompt++;
    }
    return hash;
}

int req_is_cached(const char* prompt, char* response, uint32_t* resp_len) {
    uint32_t hash = req_compute_hash(prompt);
    
    for (int i = 0; i < CACHE_SIZE; i++) {
        if (cache_valid[i] && cache_hashes[i] == hash) {
            // Return cached response
            int len = 0;
            while (cache_responses[i][len]) {
                response[len] = cache_responses[i][len];
                len++;
            }
            *resp_len = len;
            return 1;
        }
    }
    return 0;
}

void req_cache_response(const char* prompt, const char* response, uint32_t resp_len) {
    uint32_t hash = req_compute_hash(prompt);
    
    // Find empty slot or replace oldest
    int slot = cache_count % CACHE_SIZE;
    
    // Copy prompt hash and response
    cache_hashes[slot] = hash;
    for (int i = 0; prompt[i] && i < 127; i++) {
        cache_prompts[slot][i] = prompt[i];
    }
    cache_prompts[slot][127] = '\0';
    
    for (int i = 0; response[i] && i < 255 && i < (int)resp_len; i++) {
        cache_responses[slot][i] = response[i];
    }
    cache_responses[slot][255] = '\0';
    
    cache_valid[slot] = 1;
    if (cache_count < CACHE_SIZE) cache_count++;
}

route_decision_t req_analyze_and_route(optimized_request_t* req) {
    // Check if request is already cached
    char dummy[256];
    uint32_t dummy_len;
    if (req_is_cached(req->content, dummy, &dummy_len)) {
        return ROUTE_CACHE;
    }
    
    // Reject low-priority duplicate requests
    if (req->priority >= PRIORITY_LOW) {
        req->dedup_hash = req_compute_hash(req->content);
        // Check recent duplicates
        for (int i = 0; i < cache_count; i++) {
            if (cache_hashes[i] == req->dedup_hash) {
                return ROUTE_REJECT;
            }
        }
    }
    
    // Handle locally if simple
    if (req->priority == PRIORITY_CRITICAL && 
        (req->content[0] == 'i' || req->content[0] == 'h')) {
        return ROUTE_LOCAL;
    }
    
    // Route to external for complex queries
    return ROUTE_EXTERNAL;
}

int req_should_cache(const char* prompt, uint32_t* cache_idx) {
    uint32_t hash = req_compute_hash(prompt);
    
    for (int i = 0; i < CACHE_SIZE; i++) {
        if (cache_valid[i] && cache_hashes[i] == hash) {
            *cache_idx = i;
            return 1;
        }
    }
    *cache_idx = cache_count % CACHE_SIZE;
    return 0;
}

int req_create_batch(optimized_request_t* batch, uint32_t* count) {
    *count = batch_count > BATCH_SIZE ? BATCH_SIZE : batch_count;
    
    for (int i = 0; i < (int)*count; i++) {
        batch[i] = pending_batch[i];
    }
    
    batch_count = 0;
    return *count;
}

int req_send_optimized(const optimized_request_t* req) {
    // Add to batch if space
    if (batch_count < BATCH_SIZE) {
        pending_batch[batch_count] = *req;
        batch_count++;
        return 1;
    }
    
    // Send batch immediately
    // Would use network stack
    return 0;
}

uint8_t req_get_optimal_core(void) {
    // Return least loaded core
    uint64_t min_load = stats.cpu_usage[0];
    uint8_t min_core = 0;
    
    for (int i = 1; i < 256; i++) {
        if (stats.cpu_usage[i] < min_load) {
            min_load = stats.cpu_usage[i];
            min_core = i;
        }
    }
    
    return min_core;
}

void req_bind_to_core(uint32_t core_id) {
    // Set CPU affinity for current thread
    // Would use __kmp_affinity or similar
}