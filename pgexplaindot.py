#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json

def listnodes(plan, path=(0,), depth=0):
    nodename = '%s_%s' % (
        plan['Node Type'].replace(' ', '_'), '_'.join(map(str, path)))
    nodelabel = plan['Node Type']
    self = (nodename, nodelabel)
    nodes = [self]
    links = []
    for k, subplan in enumerate(plan.get('Plans', ())):
        s, n, l = listnodes(subplan, path + (k,))
        nodes.extend(n)
        links.extend(l)
        links.append((self[0], s[0]))
    return self, nodes, links

def exptree2dot(d):
    results = [
        'digraph {',
        'rankdir=LR;'
        'edge [dir="back"];'
    ]
    root, nodes, links = listnodes(d[0]['Plan'])
    for name, label in nodes:
        results.append('%s [label="%s"]' % (name, label))
    for left, right in links:
        results.append('%s -> %s' % (left, right))
    results.append('}')
    return '\n'.join(results)

if __name__ == '__main__':
    print(exptree2dot(json.loads(sys.stdin.read())))
