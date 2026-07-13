#include "database.h"
#include "../smp/smp.h"
#include <stddef.h>

static uint32_t metric_timestamp = 0;

void db_init(metric_db_t* db) {
    db->count = 0;
    db->head = 0;
    for (int i = 0; i < 1024; i++) {
        db->metrics[i].timestamp = 0;
        db->metrics[i].cpu_id = 0;
        db->metrics[i].value = 0;
    }
}

void db_add_metric(metric_db_t* db, uint32_t cpu_id, uint64_t value) {
    if (db->count < 1024) {
        db->count++;
    }
    
    db->metrics[db->head].timestamp = metric_timestamp++;
    db->metrics[db->head].cpu_id = cpu_id;
    db->metrics[db->head].value = value;
    
    db->head = (db->head + 1) % 1024;
}

metric_entry_t* db_get_latest(metric_db_t* db) {
    int idx = (db->head - 1 + 1024) % 1024;
    if (idx >= db->count) return NULL;
    return &db->metrics[idx];
}

void db_add_process(process_db_t* db, const char* name, uint32_t pid) {
    if (db->count >= 256) return;
    
    process_entry_t* p = &db->processes[db->count];
    for (int i = 0; name[i] && i < 63; i++) {
        p->name[i] = name[i];
    }
    p->name[63] = '\0';
    p->pid = pid;
    p->memory_kb = 0;
    p->cpu_affinity = 0;
    p->state = 0;
    
    db->count++;
}

void db_remove_process(process_db_t* db, uint32_t pid) {
    for (int i = 0; i < db->count; i++) {
        if (db->processes[i].pid == pid) {
            // Shift remaining entries
            for (int j = i; j < db->count - 1; j++) {
                db->processes[j] = db->processes[j + 1];
            }
            db->count--;
            break;
        }
    }
}

process_entry_t* db_find_process(process_db_t* db, uint32_t pid) {
    for (int i = 0; i < db->count; i++) {
        if (db->processes[i].pid == pid) {
            return &db->processes[i];
        }
    }
    return NULL;
}

void db_compact(metric_db_t* db) {
    // Move entries to start, remove gaps
    if (db->head == 0) return;
    
    metric_entry_t temp[1024];
    int out = 0;
    
    for (int i = 0; i < db->count; i++) {
        int idx = (db->head + i) % 1024;
        temp[out++] = db->metrics[idx];
    }
    
    for (int i = 0; i < out; i++) {
        db->metrics[i] = temp[i];
    }
    
    db->head = 0;
}

void db_build_index(process_db_t* db) {
    // Sort processes by CPU affinity for SMP optimization
    for (int i = 0; i < db->count - 1; i++) {
        for (int j = i + 1; j < db->count; j++) {
            if (db->processes[i].cpu_affinity > db->processes[j].cpu_affinity) {
                process_entry_t tmp = db->processes[i];
                db->processes[i] = db->processes[j];
                db->processes[j] = tmp;
            }
        }
    }
}