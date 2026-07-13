// LLM Merge Engine - Combine multiple models locally
#ifndef LLM_MERGE_ENGINE_H
#define LLM_MERGE_ENGINE_H

#include <stdint.h>

// Merged model result
typedef struct {
    char* output;
    uint32_t len;
    float confidence;
    uint8_t source_model; // 0=cpu, 1=gpu, 2=hybrid
} merged_result_t;

// Merge strategy
typedef enum {
    MERGE_WEIGHTED,    // Weighted average
    MERGE_CONSENSUS,   // Voting consensus
    MERGE_HIERARCHICAL // CPU pre-process, GPU refine
} merge_strategy_t;

// LLM Merge Engine
typedef struct {
    merged_result_t results[4]; // Up to 4 model outputs
    uint8_t result_count;
    merge_strategy_t strategy;
    float weights[4];
} llm_merge_engine_t;

// Functions
void merge_init(llm_merge_engine_t* engine);
void merge_add_result(llm_merge_engine_t* engine, const char* output, uint32_t len, float confidence, uint8_t model);
int merge_compute(llm_merge_engine_t* engine, char* final_output, uint32_t* final_len);

// Model comparison
float merge_calculate_confidence(const char* output1, const char* output2);
int merge_is_complementary(merged_result_t* r1, merged_result_t* r2);

// Hardware-aware merge
void merge_bind_threads(llm_merge_engine_t* engine, uint32_t core_mask);

#endif