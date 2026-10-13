#include "cache.h"
#include <vector>
#include <cstdlib>
set<uint64_t> g_pf_lines;
uint64_t g_pf_count;

static void run(const char *name, vector<int> strides, int n, uint64_t ip)
{
    CACHE c;
    g_pf_lines.clear();
    g_pf_count = 0;
    uint64_t addr = 0x100000;
    uint64_t covered = 0, total = 0;
    for (int i = 0; i < n; i++) {
        uint64_t line = addr >> 6;
        total++;
        if (g_pf_lines.count(line)) covered++;
        c.l1d_prefetcher_operate(addr, ip, 0, LOAD, 0);
        addr += (uint64_t)strides[i % strides.size()] * 64;
    }
    uint64_t useful = 0;
    for (auto l : g_pf_lines) if (l >= (0x100000 >> 6) && l < (addr >> 6)) useful++;
    printf("%-28s coverage %.1f%%  issued %lu\n", name, 100.0 * covered / total, g_pf_count);
}

int main()
{
    run("uniform +1", {1}, 20000, 0x400100);
    run("uniform +4", {4}, 20000, 0x400200);
    run("non-uniform 1,2,2,2,3", {1, 2, 2, 2, 3}, 20000, 0x400300);
    run("non-uniform 3,1,4,1,5,9,2,6", {3, 1, 4, 1, 5, 9, 2, 6}, 20000, 0x400400);
    run("non-uniform 1,1,5", {1, 1, 5}, 20000, 0x400500);
    srand(1);
    vector<int> rnd;
    for (int i = 0; i < 4096; i++) rnd.push_back(1 + rand() % 20);
    run("random strides (1..20)", rnd, 20000, 0x400600);
    CACHE c;
    c.l1d_prefetcher_final_stats();
}
