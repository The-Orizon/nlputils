
all: rmdup

rmdup: rmdup.cpp
	$(CXX) $(CXXFLAGS) -O3 -Wall -mtune=native -lxxhash -o rmdup rmdup.cpp
