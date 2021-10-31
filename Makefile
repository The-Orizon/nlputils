
all: rmdup

rmdup: rmdup.cpp
	$(CXX) $(CXXFLAGS) -O3 -Wall -mtune=native -o rmdup rmdup.cpp -lxxhash
