#include "llm_merge.h"
#include <stddef.h>

void merge_init(llm_merge_engine_t* engine) {
    engine->result_count = 0;
    engine->strategy = MERGE_WEIGHTED;
    for (int i = 0; i < 4; i++) {
        engine->weights[i] = 1.0f;
    }
}

void merge_add_result(llm_merge_engine_t* engine, const char* output, uint32_t len, float confidence, uint8_t model) {
    if (engine->result_count >= 4) return;
    
    merged_result_t* r = &engine->results[engine->result_count];
    r->output = (char*)output;
    r->len = len;
    r->confidence = confidence;
    r->source_model = model;
    
    engine->result_count++;
}

int merge_compute(llm_merge_engine_t* engine, char* final_output, uint32_t* final_len) {
    if (engine->result_count == 0) return -1;
    if (engine->result_count == 1) {
        // Single result, just copy
        merged_result_t* r = &engine->results[0];
        for (uint32_t i = 0; i < r->len && i < *final_len; i++) {
            final_output[i] = r->output[i];
        }
        *final_len = r->len;
        return 0;
    }
    
    // Weighted merge
    if (engine->strategy == MERGE_WEIGHTED) {
        // Combine outputs with weights
        float total_weight = 0;
        for (int i = 0; i < engine->result_count; i++) {
            total_weight += engine->weights[i] * engine->results[i].confidence;
        }
        
        // Select best result for now
        int best_idx = 0;
        float best_score = 0;
        for (int i = 0; i < engine->result_count; i++) {
            float score = engine->weights[i] * engine->results[i].confidence;
            if (score > best_score) {
                best_score = score;
                best_idx = i;
            }
        }
        
        merged_result_t* r = &engine->results[best_idx];
        for (uint32_t i = 0; i < r->len && i < *final_len; i++) {
            final_output[i] = r->output[i];
        }
        *final_len = r->len;
    }
    
    return 0;
}

float merge_calculate_confidence(const char* o1, const char* o2) {
    // Simple similarity metric
    int matches = 0, total = 0;
    for (int i = 0; o1[i] && o2[i] && i < 32; i++, total++) {
        if (o1[i] == o2[i]) matches++;
    }
    return (float)matches / (total > 0 ? total : 1);
}

int merge_is_complementary(merged_result_t* r1, merged_result_t* r2) {
    // Different models may provide complementary info
    return r1->source_model != r2->source_model;
}

void merge_bind_threads(llm_merge_engine_t* engine, uint32_t core_mask) {
    // Bind merge operations to specific cores
    // Would use CPU affinity syscalls
}