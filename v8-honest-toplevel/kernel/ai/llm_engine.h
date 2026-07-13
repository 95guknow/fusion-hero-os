#ifndef LLM_ENGINE_H
#define LLM_ENGINE_H

#include <stdint.h>
#include <stddef.h>

// LLM Engine Configuration
typedef struct {
    uint32_t context_size;      // Max tokens
    uint32_t threads;         // Parallel threads (use SMP)
    uint32_t batch_size;      // Inference batch
    uint32_t model_id;        // Model selector
    void* memory_pool;        // Dedicated memory
} llm_config_t;

// LLM Response Structure
typedef struct {
    char* output;
    uint32_t output_len;
    uint64_t tokens_processed;
    uint64_t execution_time_us;
} llm_response_t;

// Core LLM Functions
int llm_init(llm_config_t* config);
void llm_deinit(void);
int llm_generate(llm_response_t* resp, const char* prompt, uint32_t max_tokens);
void llm_reset_context(void);

// Optimized inference
int llm_parallel_inference(llm_response_t* resp, const char* prompts[], uint32_t num_prompts);

// Hardware-aware optimization
uint32_t llm_get_optimal_threads(void);
void llm_bind_thread_to_core(uint32_t thread_id, uint32_t core_id);

#endif