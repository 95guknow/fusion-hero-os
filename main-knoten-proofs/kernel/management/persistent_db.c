#include "persistent_db.h"
#include <stddef.h>

int pdb_init(persistent_pool_t* pool, uint64_t start, uint64_t size) {
    pool->pool_start = start;
    pool->pool_end = start + size;
    pool->pool_used = start;
    pool->entry_count = 0;
    pool->max_entries = (uint32_t)(size / 512); // Conservative
    return 0;
}

int pdb_store(persistent_pool_t* pool, const char* key, const void* data, uint32_t size, uint32_t ttl) {
    uint32_t total_size = sizeof(persist_header_t) + size;
    
    if (pool->pool_used + total_size > pool->pool_end) {
        return -1; // Out of memory
    }
    
    // Find slot
    uint32_t slot = pool->entry_count;
    persist_header_t* hdr = (persist_header_t*)(pool->pool_used);
    
    // Write header
    hdr->key_hash = req_compute_hash(key);
    hdr->timestamp_created = (uint64_t)ttl; // Simplified
    hdr->timestamp_accessed = 0;
    hdr->ttl_seconds = ttl;
    hdr->data_size = size;
    hdr->priority = 0;
    hdr->flags = 0x03; // Cached + persistent
    
    // Write data
    void* data_dest = (void*)((uint64_t)hdr + sizeof(persist_header_t));
    for (uint32_t i = 0; i < size; i++) {
        ((char*)data_dest)[i] = ((const char*)data)[i];
    }
    
    pool->pool_used += total_size;
    pool->entry_count++;
    
    return 0;
}

int pdb_load(persistent_pool_t* pool, const char* key, void* data, uint32_t* size) {
    uint32_t hash = req_compute_hash(key);
    
    for (uint64_t addr = pool->pool_start; addr < pool->pool_used; ) {
        persist_header_t* hdr = (persist_header_t*)addr;
        
        if (hdr->key_hash == hash) {
            hdr->timestamp_accessed = pool->entry_count; // Updated
            
            // Copy data
            void* src = (void*)(addr + sizeof(persist_header_t));
            uint32_t copy_size = hdr->data_size < *size ? hdr->data_size : *size;
            for (uint32_t i = 0; i < copy_size; i++) {
                ((char*)data)[i] = ((const char*)src)[i];
            }
            *size = copy_size;
            return 1;
        }
        
        addr += sizeof(persist_header_t) + hdr->data_size;
    }
    
    return 0;
}

int pdb_forget(persistent_pool_t* pool, const char* key) {
    uint32_t hash = req_compute_hash(key);
    
    for (uint64_t addr = pool->pool_start; addr < pool->pool_used; ) {
        persist_header_t* hdr = (persist_header_t*)addr;
        
        if (hdr->key_hash == hash) {
            // Mark as deleted (would move entries in real impl)
            hdr->flags = 0;
            return 1;
        }
        
        addr += sizeof(persist_header_t) + hdr->data_size;
    }
    
    return 0;
}

int pdb_evict_expired(persistent_pool_t* pool) {
    int evicted = 0;
    // Simplified: would check timestamps against TTL
    return evicted;
}

void pdb_compress_garbage(persistent_pool_t* pool) {
    // Move live entries forward, compact storage
}

int pdb_migrate_to_swap(persistent_pool_t* pool, uint32_t* migrated) {
    // Move old entries to swap storage
    *migrated = 0;
    return 0;
}