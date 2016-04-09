#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import locale
import argparse
import fileinput

preferredenc = locale.getpreferredencoding()

parser = argparse.ArgumentParser(
    description="Convert encoding of given files from one encoding to another.")
parser.add_argument(
    "-f", "--from-code", metavar='NAME', default=preferredenc,
    help="encoding of original text (locale default: %s)" % preferredenc)
parser.add_argument(
    "-t", "--to-code", metavar='NAME', default=preferredenc,
    help="encoding for output (locale default: %s)" % preferredenc)
parser.add_argument(
    "-c", metavar='errors', nargs='?', default='strict', const='ignore',
    help="set error handling scheme (default: 'strict', omitted: 'ignore')")
parser.add_argument("-o", metavar='FILE', help="output file")
parser.add_argument("FILE", nargs='*', help="input file")
args = parser.parse_args()

if args.o:
    wstream = open(args.o, 'wb')
else:
    wstream = sys.stdout.buffer

with fileinput.input(args.FILE, mode='rb') as f, wstream:
    for line in f:
        wstream.write(
            line.decode(args.from_code, args.c).encode(args.to_code, args.c))
