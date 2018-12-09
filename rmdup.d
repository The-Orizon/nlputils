import std.stdio;
import std.bitmanip;
import std.container.rbtree;
import std.digest.murmurhash;

void main(char[][] args) {
    string line;
    auto rbt = redBlackTree!(long);
    while ((line = readln()) !is null) {
        auto hash = digest!(MurmurHash3!128)(line);
        auto result = rbt.insert((cast(ubyte[])hash).peek!long());
        if (result) {
            write(line);
        }
    }
}
