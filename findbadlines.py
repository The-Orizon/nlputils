#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
This script tries to find encoding errors in stdin and prints out the bad lines.

Usage:
  python3 findbadlines.py [encoding]

The default encoding is utf-8.
'''

import sys
import codecs
import unicodedata

def replace_escape(ex):
    r = '\33[7m%s\33[0m' % ''.join('\\x%x' % b for b in ex.object[ex.start:ex.end])
    return r, ex.end

codecs.register_error('replace_escape', replace_escape)

encoding = 'utf-8'
if len(sys.argv) > 1:
    encoding = sys.argv[1]

error = False

for n, ln in enumerate(sys.stdin.buffer, 1):
    try:
        ln.decode(encoding)
    except UnicodeDecodeError:
        error = True
        sys.stdout.write('===== Bad line %d =====\n' % n)
        sys.stdout.write(ln.decode(encoding, 'replace_escape'))
        sys.stdout.flush()

sys.exit(error)
