#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import zhutil
from chardet.universaldetector import UniversalDetector

defaultenc = 'utf-8'

def listfiles(paths):
    for path in paths:
        if os.path.isfile(path):
            yield path
        elif os.path.isdir(path):
            for root, subdirs, files in os.walk(path):
                for name in files:
                    yield os.path.join(root, name)

def main(paths):
    detector = UniversalDetector()
    for filename in listfiles(paths):
        if not filename.endswith('.txt'):
            continue
        detector.reset()
        cache = []
        with open(filename, 'rb') as f:
            for line in f:
                detector.feed(line)
                cache.append(line)
                if detector.done:
                    break
            detector.close()
            for line in cache:
                sys.stdout.write(line.decode(
                    detector.result['encoding'] or defaultenc, errors='ignore'))
            for line in f:
                sys.stdout.write(line.decode(
                    detector.result['encoding'] or defaultenc, errors='ignore'))

if __name__ == '__main__':
    main(sys.argv[1:] or ['.'])
