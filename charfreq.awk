#!/usr/bin/awk -f
BEGIN {
    FS = "";
}
{
    for (i = 1; i <= NF; i++) {
        char[$i]++;
    }
}
END {
    for (i in char) {
        print char[i], i;
    }
}
