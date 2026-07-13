// Persistent Memory Database - Long-term Memory for Fusion Hero OS
#ifndef PERSISTENT_DB_H
#define PERSISTENT_DB_H

#include <stdint.h>

// Persistent Entry with TTL
typedef struct {
    uint32_t key_hash;
    uint64_t timestamp_created;
    uint64_t timestamp_accessed;
    uint32_t ttl_seconds;  // 0 = infinite
    uint32_t data_size;
    uint8_t priority;      // 0=highest, 255=discardable
    uint8_t flags;         // 0x01=cached, 0x02=persistent
} persist_header_t;

// Long-term Storage Pool
typedef struct {
    uint64_t pool_start;
    uint64_t pool_end;
    uint64_t pool_used;
    uint32_t entry_count;
    uint32_t max_entries;
} persistent_pool_t;

// Functions
int pdb_init(persistent_pool_t* pool, uint64_t start, uint64_t size);
int pdb_store(persistent_pool_t* pool, const char* key, const void* data, uint32_t size, uint32_t ttl);
int pdb_load(persistent_pool_t* pool, const char* key, void* data, uint32_t* size);
int pdb_forget(persistent_pool_t* pool, const char* key);  // Explicit deletion
int pdb_evict_expired(persistent_pool_t* pool);  // TTL cleanup

// Memory optimization
void pdb_compress_garbage(persistent_pool_t* pool);
int pdb_migrate_to_swap(persistent_pool_t* pool, uint32_t* migrated);

// Retrieval optimization
int pdb_search_prefix(persistent_pool_t* pool, const char* prefix, char* results, uint32_t* count);
int pdb_get_recent(persistent_pool_t* pool, persist_header_t* entries, uint32_t* count);

#endif