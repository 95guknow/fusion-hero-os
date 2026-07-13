#ifndef REQUEST_OPTIMIZER_H
#define REQUEST_OPTIMIZER_H

#include <stdint.h>
#include <stddef.h>

// Request priority levels
#define PRIORITY_CRITICAL 0
#define PRIORITY_HIGH     1
#define PRIORITY_NORMAL   2
#define PRIORITY_LOW      3

// Optimierte Anfrage-Struktur
typedef struct {
    char content[512];
    uint8_t priority;
    uint32_t timestamp;
    uint32_t dedup_hash;
    uint8_t retry_count;
    void* context_ptr;
} optimized_request_t;

// LLM Routing Decision
typedef enum {
    ROUTE_LOCAL,     // Handle internally
    ROUTE_EXTERNAL,  // Send to external LLM
    ROUTE_CACHE,     // Return cached response
    ROUTE_REJECT     // Drop request
} route_decision_t;

// Optimizer Functions
void req_optimizer_init(void);
route_decision_t req_analyze_and_route(optimized_request_t* req);
uint32_t req_compute_hash(const char* prompt);
int req_should_cache(const char* prompt, uint32_t* cache_idx);
int req_is_cached(const char* prompt, char* response, uint32_t* resp_len);
void req_cache_response(const char* prompt, const char* response, uint32_t resp_len);

// Batch optimization for SMP
int req_create_batch(optimized_request_t* batch, uint32_t* count);
int req_send_optimized(const optimized_request_t* req);

// Hardware-aware routing
uint8_t req_get_optimal_core(void);
void req_bind_to_core(uint32_t core_id);

#endif