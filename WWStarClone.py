#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

'''
Clone of WWStar, an ancient Classical Chinese translator.

usage: python3 WWStarClone.py [dir]
`dir` should be the root directory of WWStar, which contains a
`Script` directory.

Copyright (c) 2016 gumblex

This program is free software. It comes without any warranty, to
the extent permitted by applicable law. You can redistribute it
and/or modify it under the terms of the Do What The Fuck You Want
To Public License, Version 2, as published by Sam Hocevar. See
http://www.wtfpl.net/ for more details.
'''

class WWStarEngine:
    def __init__(self, path):
        self.datadir = os.path.join(path, 'Script')
        self.d = {}
        self.maxlen = 1
        self.version = open(os.path.join(self.datadir, 'VERSION.DAT'), 'r', encoding='gbk').read().splitlines()
        prefix = self.version[4]
        for fn in sorted(os.listdir(self.datadir)):
            if fn.lower().startswith(prefix.lower()) and fn[-1].isdigit():
                # ignore WWS.RT
                self.load_file(os.path.join(self.datadir, fn))

    def load_file(self, filename):
        word_len = int(filename[-1])
        with open(filename, 'r', encoding='gbk') as f:
            while 1:
                s = f.readline()
                t = f.readline()
                if s and t:
                    s = s.strip()
                    # makes the behavior for conflict phrases the same as WWStar
                    if len(s) == word_len and s not in self.d:
                        self.d[s] = t.strip()
                    self.maxlen = max(self.maxlen, len(s))
                else:
                    break

    def translate(self, sentence):
        n = len(sentence)
        pos = 0
        while pos < n:
            i = pos
            frag = sentence[pos]
            maxword = None
            maxpos = 0
            while i < n and i < pos + self.maxlen:
                if frag in self.d:
                    maxword = frag
                    maxpos = i
                i += 1
                frag = sentence[pos:i+1]
            if maxword is None:
                yield sentence[pos]
                pos += 1
            else:
                yield self.d[maxword]
                pos = maxpos + 1

if __name__ == '__main__':
    if len(sys.argv) == 1:
        path = '.'
    else:
        path = sys.argv[1]
    te = WWStarEngine(path)
    for ln in sys.stdin:
        print(''.join(te.translate(ln.rstrip())))
