#!/usr/bin/awk -f
{
    for (i = 1; i <= NF; i++) {
        word[$i]++;
    }
}
END {
    for (i in word) {
        print word[i], i;
    }
}
