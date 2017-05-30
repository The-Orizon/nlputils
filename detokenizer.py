#!/usr/bin/env python3
import sys, os, re
from pangu import spacing

RE_WS_IN_FW = re.compile(r'([\u2018\u2019\u201c\u201d\u2e80-\u312f\u3200-\u32ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef])\s+(?=[\u2018\u2019\u201c\u201d\u2e80-\u312f\u3200-\u32ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef])')

detokenize = lambda s: spacing(RE_WS_IN_FW.sub(r'\1', s)).strip()

for ln in sys.stdin:
	l = ln.strip()
	sys.stdout.write(detokenize(l) + '\n')
sys.stdout.flush()
