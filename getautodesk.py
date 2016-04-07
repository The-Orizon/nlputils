#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

pairs = []

lng = sys.argv[1].split('.')[0]

def uniq(seq):
	seen = set()
	seen_add = seen.add
	return [x for x in seq if not (x in seen or seen_add(x))]

with open('autodesk.eng-%s.%s' % (lng, lng), 'w') as tgt, open('autodesk.eng-%s.eng' % lng, 'w') as src:
	for fn in sys.argv[1:]:
		with open(fn, 'r') as f:
			for ln in f.read().split('\uF8FF◊÷\n'):
				if not ln:
					continue
				fields = ln.split('\uF8FF')
				pairs.append((fields[0], fields[2]))

	pairs = uniq(pairs)
	
	for s, t in pairs:
		src.write(s + '\n')
		tgt.write(t + '\n')
