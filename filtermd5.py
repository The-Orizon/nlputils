#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import hashlib
import binascii

md5s = set()

with open(sys.argv[1], 'rb') as f:
    for ln in f:
        md5s.add(hashlib.md5(ln.rstrip(b'\n')).digest())

for ln in sys.stdin.buffer:
    try:
        m = binascii.a2b_hex(ln.rstrip(b'\n').split(b':')[-1])
    except Exception:
        continue
    if m not in md5s:
        sys.stdout.buffer.write(ln)

