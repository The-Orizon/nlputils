#!/usr/bin/awk -f
# usage: awk -f ngramfreq.awk -v N=2
BEGIN {
    FS = "";
    # N = 2; # change this or specify in arguments
}
{
    for (i = 1; i <= NF-N+1; i++) {
        frag = "";
        for (j = 0; j < N; j++) {
            frag = frag $(i+j);
        }
        ngram[frag]++;
    }
}
END {
    for (i in ngram) {
        print ngram[i], i;
    }
}
