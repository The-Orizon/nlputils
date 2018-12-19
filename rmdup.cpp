#include <iostream>
#include <string>
#include <unordered_set>
extern "C" {
    #include "xxhash.h"
}

typedef unsigned long long u64;

int main() {
    std::string line;
    std::unordered_set<u64> lset;
    u64 hash;
    while (std::getline(std::cin, line)) {
        hash = XXH64(line.c_str(), line.length(), 64);
        if (lset.insert(hash).second) {
            std::cout << line << std::endl;
        }
    }
}
