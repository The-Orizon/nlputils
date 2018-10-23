#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

class PhraseCombiner:
    def __init__(self, dictfile, char=''):
        self.pfdic = {}
        self.char = char
        with open(dictfile, 'r') as f:
            for ln in f:
                word = ln.strip()
                for index in range(len(word) - 1):
                    if word[:index+1] not in self.pfdic:
                        self.pfdic[word[:index + 1]] = 0
                self.pfdic[word] = 1

    def combine(self, tokens):
        N = len(tokens)
        pos = 0
        res = []
        while pos < N:
            i = pos
            frag = tokens[pos]
            maxph = None
            maxpos = 0
            while i < N and frag in self.pfdic:
                if self.pfdic[frag]:
                    maxph = frag
                    maxpos = i
                i += 1
                frag = self.char.join(tokens[pos:i+1])
            if maxph is None:
                maxph = tokens[pos]
                pos += 1
            else:
                pos = maxpos + 1
            res.append(maxph)
        return res


def main(dictfile):
    pc = PhraseCombiner(dictfile, '')
    for ln in sys.stdin:
        tks = ln.strip().split()
        print(' '.join(pc.combine(tks)))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
