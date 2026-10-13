#pragma once
#include <cstdint>
#include <iostream>
#include <set>
using namespace std;
#define LOAD 0
#define RFO 1
#define PREFETCH 2
#define FILL_L1 1
#define FILL_L2 2
#define LOG2_BLOCK_SIZE 6
#define LOG2_PAGE_SIZE 12
extern set<uint64_t> g_pf_lines;
extern uint64_t g_pf_count;
class CACHE {
  public:
    uint32_t cpu = 0;
    uint64_t pf_issued = 0, pf_useful = 0, pf_fill = 0, pf_requested = 0;
    struct { int occupancy = 0; int SIZE = 8; } MSHR;
    int prefetch_line(uint64_t ip, uint64_t base, uint64_t pf, int fl, uint32_t md) { g_pf_lines.insert(pf >> 6); g_pf_count++; return 1; }
    void l1d_prefetcher_initialize();
    void l1d_prefetcher_operate(uint64_t addr, uint64_t ip, uint8_t cache_hit, uint8_t type, uint8_t critical_ip_flag);
    void l1d_prefetcher_notify_about_dtlb_eviction(uint64_t addr, uint32_t set, uint32_t way, uint8_t prefetch, uint64_t evicted_addr, uint32_t metadata_in);
    void l1d_prefetcher_cache_fill(uint64_t v_addr, uint64_t addr, uint32_t set, uint32_t way, uint8_t prefetch, uint64_t v_evicted_addr, uint64_t evicted_addr, uint32_t metadata_in);
    void l1d_prefetcher_final_stats();
};
