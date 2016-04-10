#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import zhconv
import zhutil
import argparse
import multiprocessing
from chardet.universaldetector import UniversalDetector

def listfiles(paths):
    for path in paths:
        if os.path.isfile(path):
            yield path
        elif os.path.isdir(path):
            for root, subdirs, files in os.walk(path):
                for name in files:
                    yield os.path.join(root, name)

def convertfunc(s, locale):
    if locale:
        simp = zhconv.issimp(s, True)
        if (simp is None
            or simp and locale in zhconv.Locales['zh-hans']
            or locale in zhconv.Locales['zh-hant']):
            return lambda x: x
        else:
            return lambda x: zhconv.convert(s, locale)
    else:
        return lambda x: x

def detect_convert(filename):
    detector = UniversalDetector()
    detector.reset()
    cache = b''
    with open(filename, 'rb') as f:
        for line in f:
            detector.feed(line)
            cache += line
            if detector.done:
                break
        detector.close()
        cache = cache.decode(
            detector.result['encoding'] or args.fallback_enc,
            errors='ignore')
        cf = convertfunc(cache, args.locale)
        yield cf(cache)
        for line in f:
            yield cf(line.decode(
                detector.result['encoding'] or args.fallback_enc,
                errors='ignore'))

def detect_convert_str(filename):
    return zhutil.fw2hw(''.join(detect_convert(filename)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Merge a txt file collection to one large corpus.")
    #parser.add_argument(
        #"-e", "--encoding", metavar='NAME',
        #help="encoding of original text (default: auto-detect)")
    parser.add_argument(
        "--fallback-enc", default='utf-8',
        help="fallback encoding (default: utf-8)")
    parser.add_argument(
        "-l", "--locale",
        help="Chinese variant conversion (default: no conversion)")
    parser.add_argument("-o", metavar='FILE', help="output file")
    parser.add_argument("PATH", default='.', nargs='*', help="input path (can be directory)")
    args = parser.parse_args()
    pool = multiprocessing.Pool()
    if args.o:
        wstream = open(args.o, 'w', encoding='utf-8')
    else:
        wstream = sys.stdout
    files = [fn for fn in listfiles(args.PATH) if fn.endswith('.txt')]
    with wstream:
        for r in pool.imap_unordered(detect_convert_str, files):
            wstream.write(r)
