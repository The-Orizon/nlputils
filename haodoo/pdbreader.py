#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import struct

class PdbFile:

    charmap_h = str.maketrans(
        '︿﹀︽︾﹁﹂﹃﹄︻︼︗︘︹︺︵︶︷︸﹇﹈｜│︙￤ⸯ',
        '〈〉《》「」『』【】〖〗〔〕（）｛｝［］—………～'
    )
    charmap_v = str.maketrans(
        '"\'()-—‘’“”…〈〉《》「」『』【】〔〕（）｛｝',
        '﹁﹃︵︶｜｜﹃﹄﹁﹂│︿﹀︽︾﹁﹂﹃﹄︻︼︹︺︵︶︷︸'
    )

    def __init__(self, filename=None, fixpunct=False):
        self.title = None
        self.author = None
        self.contents = []
        self.text = []
        self.bookmarks = None
        if filename:
            self.load(filename)
        if fixpunct:
            self.punct_convert(False)

    def load(self, filename):
        with open(filename, 'rb') as f:
            header = f.read(78)
            if header[60:68] == b'BOOKMTIT':
                encoding = 'cp950'
            elif header[60:68] == b'BOOKMTIU':
                encoding = 'utf_16_le'
            else:
                raise AssertionError('file type not recognized')
            if header[35] == 2:
                self.author = header[:35].rstrip(b'\0').decode(encoding, 'replace')
            recordnum = struct.unpack('>H', header[76:78])[0]
            locations = []
            lastloc = None
            for i in range(recordnum):
                loc = struct.unpack('>I', f.read(8)[:4])[0]
                if lastloc:
                    locations.append((lastloc, loc-lastloc))
                lastloc = loc
            if lastloc:
                # last record: bookmarks
                locations.append((lastloc, None))
            for k, (loc, length) in enumerate(locations):
                val = f.read(length)
                if k:
                    if length:
                        self.text.append(val.decode(encoding, 'replace').rstrip('\0'))
                    else:
                        try:
                            self.bookmarks = list(struct.unpack(
                                '<' + 'h'*(len(val)//2), val)[:-1])
                        except Exception:
                            pass
                elif encoding == 'cp950':
                    title, other = val[8:].split(b'\x1B\x1B\x1B', 1)
                    self.title = title.decode(encoding, 'replace')
                    chapternum, chapters = other.split(b'\x1B', 1)
                    chapternum = int(chapternum.decode('ascii'))
                    self.contents = chapters.decode(encoding, 'replace').split('\x1B')
                else:
                    title, other = val[8:].split(b'\x1B\x00\x1B\x00\x1B\x00', 1)
                    self.title = title.decode(encoding, 'replace')
                    chapternum, chapters = other.split(b'\x1B\x00', 1)
                    chapternum = int(chapternum.decode('ascii'))
                    self.contents = chapters.decode(encoding, 'replace').split('\r\n')
            # len(self.contents) may be less than chapter number
            assert recordnum-2 == chapternum == len(self.text)

    def punct_convert(self, tovertical=False):
        if tovertical:
            charmap = self.charmap_v
        else:
            charmap = self.charmap_h
        self.title = self.title.translate(charmap)
        if self.author:
            self.author = self.author.translate(charmap)
        self.contents = [s.translate(charmap) for s in self.contents]
        self.text = [s.translate(charmap) for s in self.text]

    def dump(self, filename, big5=False):
        with open(filename, 'wb') as f:
            encoding = 'cp950' if big5 else 'utf_16_le'
            if self.author:
                f.write(self.author.encode(encoding, 'replace').ljust(35, b'\0') + b'\2')
            else:
                f.write(self.title.encode(encoding, 'replace').ljust(35, b'\0') + b'\1')
            f.write(b'\x3B\x29\x9B\xE5\x3B\x29\x9B\xE5' + b'\0'*16)
            if big5:
                f.write(b'BOOKMTIT')
            else:
                f.write(b'BOOKMTIU')
            f.write(b'\0'*8)
            recordnum = len(self.text) + 2
            f.write(struct.pack('>H', recordnum))
            posstart = f.tell()
            f.write(b'\0'*(recordnum*8))
            positions = [f.tell()]
            f.write(b' '*8)
            f.write((self.title + '\x1B\x1B\x1B').encode(encoding, 'replace'))
            f.write(str(len(self.text)).encode('ascii'))
            if big5:
                f.write(('\x1B' + '\x1B'.join(self.contents)).encode(encoding, 'replace'))
            else:
                f.write(('\x1B' + '\r\n'.join(self.contents)).encode(encoding, 'replace'))
            positions.append(f.tell())
            for chapter in self.text:
                f.write(chapter.encode(encoding, 'replace'))
                if big5:
                    f.write(b'\0')
                positions.append(f.tell())
            if self.bookmarks:
                f.write(struct.pack('<' + 'h'*(len(self.bookmarks)), *self.bookmarks))
            f.write(b'\xFF\xFF')
            f.seek(posstart)
            for pos in positions:
                f.write(struct.pack('>I', pos) + b'\0'*4)

    def save_txt(self, filename, encoding='utf-8'):
        with open(filename, 'w', encoding=encoding) as f:
            f.write('\r\n\r\n\r\n\r\n'.join(self.text))

if __name__ == '__main__':
    import sys
    pf = PdbFile(sys.argv[1], True)
    pf.save_txt(sys.argv[1].rsplit('.', 1)[0] + '.txt')
