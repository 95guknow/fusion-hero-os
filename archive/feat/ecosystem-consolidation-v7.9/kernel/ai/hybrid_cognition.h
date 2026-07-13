// CPU/GPU Hybrid Architecture - Fusion Hero OS
#ifndef HYBRID_COGNITION_H
#define HYBRID_COGNITION_H

#include <stdint.h>

// CPU Role: Fast Computation, Logic, Immediate Responses
// GPU Role: Parallel Processing, Complex Reasoning, Embeddings

// CPU Task Types
typedef enum {
    CPU_TASK_MATH,
    CPU_TASK_LOGIC,
    CPU_TASK_IO,
    CPU_TASK_CACHE_LOOKUP,
    CPU_TASK_SIMPLE_QUERY,
    CPU_TASK_SCHEDULING
} cpu_task_type_t;

// GPU Task Types  
typedef enum {
    GPU_TASK_EMBEDDING,
    GPU_TASK_REASONING,
    GPU_TASK_PATTERN_MATCH,
    GPU_TASK_COMPLEX_INFERENCE,
    GPU_TASK_MEMORY_ASSOCIATION,
    GPU_TASK_CONTEXT_MERGE
} gpu_task_type_t;

// Task Structures
typedef struct {
    uint32_t id;
    cpu_task_type_t type;
    void* args;
    uint32_t arg_size;
    void* result;
    uint8_t core_affinity;
    uint8_t priority;
} cpu_task_t;

typedef struct {
    uint32_t id;
    gpu_task_type_t type;
    void* data;
    uint32_t data_size;
    void* result;
    uint8_t thread_group;  // Multiple GPU cores
    uint8_t priority;
} gpu_task_t;

// Hybrid Engine
typedef struct {
    void* cpu_queue;
    void* gpu_queue;
    uint32_t cpu_load[256];
    uint32_t gpu_load[256];
    uint8_t mode;  // 0=auto, 1=cpu-first, 2=gpu-first
} hybrid_engine_t;

// Functions
void hybrid_init(hybrid_engine_t* eng);
void cpu_enqueue(hybrid_engine_t* eng, const cpu_task_t* task);
void gpu_enqueue(hybrid_engine_t* eng, const gpu_task_t* task);
int hybrid_decide_route(const char* query);  // Returns 0=CPU, 1=GPU

// CPU optimized for speed
int cpu_execute_math(double a, double b, char op, double* result);
int cpu_execute_logic(const char* condition, int* result);

// GPU optimized for parallel thinking
int gpu_execute_embedding(const char* text, float* vector, uint32_t dim);
int gpu_reason_about_context(const char* context, char* conclusion, uint32_t* len);

// Memory allocation strategy
void* hybrid_alloc(uint32_t size, uint8_t type); // type: 0=shared, 1=cpu, 2=gpu
void hybrid_free(void* ptr, uint8_t type);

#endif