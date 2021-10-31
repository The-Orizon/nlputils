#include <iostream>
#include <string>
#include <unordered_set>
extern "C" {
    #include "xxhash.h"
}

int main() {
    std::string line;
    std::unordered_set<XXH64_hash_t> lset;
    XXH64_hash_t hash;
    while (std::getline(std::cin, line)) {
        hash = XXH64(line.c_str(), line.length(), 64);
        if (lset.insert(hash).second) {
            std::puts(line.c_str());
        }
    }
}
