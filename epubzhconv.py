#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import zipfile
import collections
import xml.dom.minidom
import zhconv

def convertepub(filename, output, locale):
    with zipfile.ZipFile(filename, 'r') as zf, \
         zipfile.ZipFile(output, 'w') as zw:
        zfiles = collections.OrderedDict()
        for zi in zf.infolist():
            zfiles[zi.filename] = zi
        with zf.open(zfiles['META-INF/container.xml'], 'r') as f:
            dom = xml.dom.minidom.parse(f)
            rootfiles = [t.getAttribute('full-path')
                for t in dom.getElementsByTagName('rootfile')
                if t.getAttribute('media-type') == 'application/oebps-package+xml']
        htmls = set(rootfiles)
        for rootfile in rootfiles:
            with zf.open(zfiles[rootfile], 'r') as f:
                dom = xml.dom.minidom.parse(f)
                manifest = dom.getElementsByTagName('manifest')[0]
                htmls.update(t.getAttribute('href')
                    for t in manifest.getElementsByTagName('item')
                    if t.getAttribute('media-type') in
                    ('application/xhtml+xml', 'application/x-dtbncx+xml'))
        for name, zi in zfiles.items():
            if name in htmls:
                s = zhconv.convert(zf.read(zi).decode('utf-8'), locale)
                zw.writestr(zi, s.encode('utf-8'))
            else:
                zw.writestr(zi, zf.read(zi))

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('usage: python3 epubzhconv.py input.epub output.epub locale')
        sys.exit(1)
    convertepub(*sys.argv[1:])
