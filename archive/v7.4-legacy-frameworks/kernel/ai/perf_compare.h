// LLM Performance Comparison and Hardware-Acceleration
#ifndef PERF_COMPARE_H
#define PERF_COMPARE_H

#include <stdint.h>

// Model Benchmark Results
typedef struct {
    char model_name[64];
    uint64_t tokens_per_sec;
    uint64_t latency_ms;
    uint8_t cores_used;
    uint8_t quality_score; // 0-100
    uint8_t energy_eff;    // 0-100
} model_benchmark_t;

// Hardware Capability Detection
typedef struct {
    uint32_t simd_support;  // AVX, SSE
    uint32_t core_count;
    uint32_t thread_count;
    uint64_t cache_l1_kb;
    uint64_t cache_l2_kb;
    uint64_t cache_l3_kb;
} hw_caps_t;

// Comparison Functions
void perf_detect_hw_caps(hw_caps_t* caps);
int perf_compare_models(model_benchmark_t* results, uint32_t count);
int perf_select_best_model(model_benchmark_t* results, uint32_t count, hw_caps_t* caps);
int perf_test_local_model(char* output, uint32_t* out_len, const char* prompt);

// Hardware-Accelerated Inference
int perf_avx_inference(const char* prompt, char* output, uint32_t* out_len);
int perf_simd_tokenize(const char* input, uint32_t* tokens, uint32_t* count);

#endif