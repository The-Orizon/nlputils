#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import uuid
import html
import sqlite3
import zipfile
import pdbreader

re_haodooid = re.compile('[A-J][0-9A-Za-z]{2,10}')

_cnums = '○一二三四五六七八九十'

re_bookdate = re.compile('《([%s]{4})年([%s]{1,3})月([%s]{1,3})日版》' % ((_cnums,)*3))
re_parasplit = re.compile('(.+\n+)')
re_paranewline = re.compile('^(.+)(\n*)')
re_booktitle = re.compile('^《(.+)》(.+)$')

re_chaptersplit = re.compile('　　※※※')

EPUB_container_xml = b"""<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
 <rootfiles>
  <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
 </rootfiles>
</container>
"""

EPUB_stylesheet_css = b"""body {
margin-left: 5%; margin-right: 5%; margin-top: 5%; margin-bottom: 5%; text-align: justify;}
h1,h2 {text-align: center;}
.center {text-align: center;}
.right {text-align: right;}
p {margin: 1em 0;}
"""

EPUB_cover_page = b"""<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
        <meta name="calibre:cover" content="true"/>
        <title>Cover</title>
        <style type="text/css" title="override_css">
            @page {padding: 0pt; margin:0pt}
            body { text-align: center; padding:0pt; margin: 0pt; }
        </style>
    </head>
    <body>
        <div>
            <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="100%" height="100%" viewBox="0 0 180 263" preserveAspectRatio="none">
                <image width="180" height="263" xlink:href="cover.jpeg"/>
            </svg>
        </div>
    </body>
</html>
"""

_cnum_map = {
    (lambda d: ((((_cnums[d[0]] if d[0] > 1 else '') + _cnums[10])
        if d[0] else '') + (_cnums[d[1]] if not d[0] or d[1] else ''))
    )(divmod(i, 10)): i for i in range(32)
}

date_conv = lambda s: (lambda m: '%s-%02d-%02d' % (''.join(map(str,
    map(_cnum_map.__getitem__, m.group(1)))),
    _cnum_map[m.group(2)], _cnum_map.get(m.group(3), 1)) if m else None)(
    re_bookdate.search(s))

def content_opf(metadata, chapternum):
    opf = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<package version="2.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">',
        ' <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">',
        '  <dc:title>%s</dc:title>' % metadata['title'],
        '  <dc:creator opf:role="aut">%s</dc:creator>' % metadata['author'],
        '  <dc:language>zh-TW</dc:language>',
        '  <dc:identifier opf:scheme="uuid" id="uuid_id">%s</dc:identifier>' % metadata['uuid'],
    ]
    if 'id' in metadata:
        opf.append('  <dc:identifier opf:scheme="haodoo" id="haodoo_id">%s</dc:identifier>' % metadata['id'])
    if metadata.get('date'):
        opf.append('  <dc:date>%sT00:00:00+00:00</dc:date>' % metadata['date'])
    if 'category' in metadata:
        opf.append('  <dc:subject>%s</dc:subject>' % metadata['category'])
    if 'description' in metadata:
        opf.append('  <dc:description>%s</dc:description>' %
            html.escape(metadata['description'], False))
    if 'img' in metadata:
        opf.append('  <meta name="cover" content="cover"/>')
    opf.append(' </metadata>')
    opf.append(' <manifest>')
    if 'img' in metadata:
        opf.append('  <item href="cover.jpeg" id="cover" media-type="image/jpeg"/>')
        opf.append('  <item href="titlepage.xhtml" id="titlepage" media-type="application/xhtml+xml"/>')
    opf.append('  <item href="toc.ncx" id="ncx" media-type="application/x-dtbncx+xml"/>')
    opf.append('  <item href="stylesheet.css" id="css" media-type="text/css"/>')
    for i in range(chapternum+1):
        opf.append('  <item id="P%03d" href="%03d.html" media-type="application/xhtml+xml"/>' % (i, i))
    opf.append(' </manifest>')
    opf.append(' <spine toc="ncx">')
    if 'img' in metadata:
        opf.append('  <itemref idref="titlepage"/>')
    for i in range(chapternum+1):
        opf.append('  <itemref idref="P%03d"/>' % i)
    opf.append(' </spine>')
    opf.append(' <guide>')
    if 'img' in metadata:
        opf.append('  <reference href="titlepage.xhtml" title="Cover" type="cover"/>')
    opf.append('  <reference href="000.html" title="start" type="text"/>')
    opf.append(' </guide>')
    opf.append('</package>\n')
    return '\n'.join(opf).encode('utf-8')

def toc_ncx(metadata, chapters):
    toc = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh-TW">',
        ' <head>',
        '  <meta name="dtb:uid" content="%s"/>' % metadata['uuid'],
        '  <meta name="dtb:depth" content="1"/>',
        '  <meta name="dtb:totalPageCount" content="0"/>',
        '  <meta name="dtb:maxPageNumber" content="0"/>',
        ' </head>',
        ' <docTitle><text>%s</text></docTitle>' % html.escape(metadata['title']),
        ' <navMap>',
    ]
    chapters = ('目錄',) + tuple(chapters)
    for k, chapter in enumerate(chapters):
        toc.append(' <navPoint id="%d" playOrder="%d">' % (k, k))
        toc.append('  <navLabel><text>%s</text></navLabel>' % chapter)
        toc.append('  <content src="%03d.html"/>' % k)
        toc.append(' </navPoint>')
    toc.append(' </navMap>\n</ncx>\n')
    return '\n'.join(toc).encode('utf-8')

def toc_html(metadata, chapters):
    toc = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-TW">',
        '<head><title>%s</title>' % html.escape(metadata['title']),
        '<link href="stylesheet.css" type="text/css" rel="stylesheet"/>',
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>',
        '</head><body>',
        '<h1>%s</h1>' % html.escape(metadata['title']),
        '<p class="center">%s</p>' % html.escape(metadata['author']),
        '<h2>目錄</h2>',
        '<ul>'
    ]
    for k, chapter in enumerate(chapters, 1):
        toc.append('<li><a href="%03d.html">%s</a></li>' % (k, chapter))
    toc.append('</ul>\n</body>\n')
    return '\n'.join(toc).encode('utf-8')

def makehtml(chapternum, title, txt):
    started = False
    firsttitle = False
    paranum = 0
    result = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-TW">',
        '<head><title>%s</title>' % html.escape(title),
        '<link href="stylesheet.css" type="text/css" rel="stylesheet"/>',
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>',
        '</head><body>',
    ]
    p = []
    txt = txt.replace('\r\n', '\n').strip() + '\n\n'
    for para in re_parasplit.split(txt):
        if not para:
            continue
        para, newline = re_paranewline.match(para).groups()
        nlnum = len(newline)
        if paranum == 0:
            if chapternum == 1:
                title = para
                author = None
                match = re_booktitle.match(para)
                if match:
                    title, author = match.groups()
                result.append('<h1>%s</h1>' % html.escape(title))
                result.append('<p class="right">')
                if author:
                    p.append(html.escape(author))
            else:
                result.append('<h2>%s</h2>' % html.escape(para.strip()))
                started = firsttitle = True
        elif not started:
            if re_bookdate.match(para):
                p.append(html.escape(para.strip('《》')))
            else:
                p.append(html.escape(para))
            if nlnum > 1:
                result.append('<br/>'.join(p))
                result.append('</p>')
                p = []
                started = True
        elif not firsttitle:
            result.append('<h2>%s</h2>' % html.escape(para))
            firsttitle = True
        else:
            if para.endswith('※※※'):
                result.append('<p class="center">※　※　※</p>')
            elif not para.startswith('　　') and nlnum > 1:
                result.append('<h3>%s</h3>' % html.escape(para))
            elif nlnum > 1:
                if p:
                    p.append(html.escape(para))
                    result.append('<br/>'.join(p))
                    result.append('</p>')
                    p = []
                else:
                    result.append('<p>%s</p>' % html.escape(para))
            else:
                p.append(html.escape(para))
        paranum += 1
    if p:
        result.append('<br/>'.join(p))
        result.append('</p>')
    result.append('</body></html>\n')
    return '\n'.join(result).encode('utf-8')

def pdb2epub(pdbfile, epubfile, haodoodb=None):
    pdb = pdbreader.PdbFile(pdbfile, True)
    metadata = {
        'title': pdb.title or '',
        'author': pdb.author or '',
        'uuid': str(uuid.uuid4())
    }
    filename = os.path.basename(pdbfile)
    fileid, filetype = os.path.splitext(filename)
    filetype = filetype.lstrip('.').lower()
    if filetype not in ('pdb', 'updb'):
        raise ValueError('input file must be pdb or updb')
    if haodoodb:
        db = sqlite3.connect(haodoodb)
        dbresult = db.execute(
            "SELECT b.id, s.category, "
            "  coalesce(f.update_date, f.add_date), s.description, c.img "
            "FROM books b "
            "INNER JOIN series s USING (series) "
            "INNER JOIN files f ON f.bookid=b.id "
            "LEFT JOIN covers c USING (series) "
            "WHERE f.type=? AND "
            "  (f.downloadname=? OR b.series=? OR (b.title=? AND b.author=?)) "
            "ORDER BY c.filename",
            (filetype, filename, filename, pdb.title, pdb.author)
        ).fetchone()
        if dbresult:
            (metadata['id'], metadata['category'], metadata['date'],
             metadata['description'], metadata['img']) = dbresult
            if metadata['img'] is None:
                del metadata['img']
    else:
        if re_haodooid.match(fileid):
            metadata['id'] = fileid
    bookdate = date_conv(pdb.text[0])
    if bookdate:
        metadata['date'] = bookdate
    with zipfile.ZipFile(epubfile, 'w') as zw:
        zw.writestr("mimetype", b"application/epub+zip", zipfile.ZIP_STORED)
        zw.writestr("META-INF/container.xml", EPUB_container_xml)
        zw.writestr("content.opf", content_opf(metadata, len(pdb.contents)))
        if 'img' in metadata:
            zw.writestr("cover.jpeg", metadata['img'])
        zw.writestr("toc.ncx", toc_ncx(metadata, pdb.contents))
        zw.writestr("stylesheet.css", EPUB_stylesheet_css)
        if 'img' in metadata:
            zw.writestr("titlepage.xhtml", EPUB_cover_page)
        zw.writestr("000.html", toc_html(metadata, pdb.contents))
        for k, text in enumerate(pdb.text, 1):
            try:
                title = pdb.contents[k]
            except IndexError:
                title = ''
            zw.writestr("%03d.html" % k, makehtml(k, title, text))

if __name__ == '__main__':
    pdb2epub(*sys.argv[1:])
