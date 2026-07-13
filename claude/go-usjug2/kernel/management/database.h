#ifndef DATABASE_H
#define DATABASE_H

#include <stdint.h>

// Simple embedded key-value database for process/storage tracking
typedef struct {
    uint32_t timestamp;
    uint32_t cpu_id;
    uint64_t value;
} metric_entry_t;

typedef struct {
    metric_entry_t metrics[1024];
    uint16_t count;
    uint16_t head;
} metric_db_t;

typedef struct {
    char name[64];
    uint32_t pid;
    uint64_t memory_kb;
    uint8_t cpu_affinity;
    uint8_t state; // 0=running, 1=idle, 2=sleep
} process_entry_t;

typedef struct {
    process_entry_t processes[256];
    uint8_t count;
} process_db_t;

// Database operations
void db_init(metric_db_t* db);
void db_add_metric(metric_db_t* db, uint32_t cpu_id, uint64_t value);
metric_entry_t* db_get_latest(metric_db_t* db);
void db_add_process(process_db_t* db, const char* name, uint32_t pid);
void db_remove_process(process_db_t* db, uint32_t pid);
process_entry_t* db_find_process(process_db_t* db, uint32_t pid);

// Optimization functions
void db_compact(metric_db_t* db);
void db_build_index(process_db_t* db);

#endif