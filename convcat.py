#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
from chardet.universaldetector import UniversalDetector

detector = UniversalDetector()

arg = sys.argv[1:]
if arg:
    fns = list(filter(os.path.isfile, arg))
else:
    fns = ['-']

for fn in fns:
    if fn == '-':
        stream = sys.stdin.buffer
    else:
        stream = open(fn, 'rb')
    detector.reset()
    cache = []
    for line in stream:
        detector.feed(line)
        cache.append(line)
        if detector.done:
            break
    detector.close()
    for line in cache:
        sys.stdout.write(line.decode(detector.result['encoding'] or 'utf-8', errors='replace'))
    for line in stream:
        sys.stdout.write(line.decode(detector.result['encoding'] or 'utf-8', errors='replace'))
    stream.close()
