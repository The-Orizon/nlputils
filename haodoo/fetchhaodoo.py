#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import time
import sqlite3
import logging
import requests
import datetime
import urllib.parse
import concurrent.futures
import bs4

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-TW,zh;q=0.8,zh-CN;q=0.6,en;q=0.4",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36",
}

logging.basicConfig(stream=sys.stderr, format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

re_title = re.compile('(.+?)[【《](.+)[》】]')
re_script = re.compile(r'SetTitle\("(.+?)[【《](.+)[》】]"\).+\'<a href=.+>(\w+)( +書目)?</a>\'', re.DOTALL)
re_script2 = re.compile(r'(\w+) +書目|SetLink\(\'<a href=.+>(\w+)</a>\'\);')
re_scriptlink = re.compile(r'<a href="([^"]+)">.+?</a>')
re_onclick = re.compile(r"(\w+)\('([^']+)'.*\)")
re_date = re.compile('\d{4}/\d{1,2}/\d{1,2}')
re_corrtable = re.compile(r'^\s*勘誤表：\n*')
re_corrtable_txt = re.compile(r'勘誤表')
re_quality1 = re.compile(r'[【《]經典版[》】]')
re_quality2 = re.compile(r'[【《]典藏版[》】]')
re_newlines = re.compile(r'\n{3,}')
re_audiobooktitle = re.compile(r'^(.+)?[【《](.+)[》】](?:（.+）)?(?:(.+)錄音)?$')
re_audiobookchapter = re.compile(r'^([^【《]*)[【《](.+)[》】](.+)錄音\s*(\d{4}/\d{1,2}/\d{1,2})')
re_audiobookchapter2 = re.compile(r'^()[【《]?(.+)[》】](.+)錄音\s*(\d{4}/\d{1,2}/\d{1,2})')
re_recorder = re.compile(r'(\w+)錄音')

parse_page = lambda url: urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)['P'][0]
date_fmt = lambda s: '%04d-%02d-%02d' % tuple(map(int, s.split('/')))
parse_date = lambda s: int(datetime.datetime.strptime(s, '%a, %d %b %Y %X %Z').timestamp())

class HaodooCrawler:

    root = 'http://www.haodoo.net/'

    def __init__(self, db='haodoo.db'):
        self.db = sqlite3.connect(db)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.executor = concurrent.futures.ThreadPoolExecutor(6)

    def init_db(self):
        cur = self.db.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS links ('
            'url TEXT PRIMARY KEY,'
            'updated INTEGER'
        ')')
        cur.execute(
            'CREATE INDEX IF NOT EXISTS idx_links '
            'ON links (updated)'
        )
        cur.execute('CREATE TABLE IF NOT EXISTS covers ('
            'filename TEXT PRIMARY KEY,'
            'series TEXT,'
            'modified INTEGER,'
            'img BLOB'
        ')')
        cur.execute('CREATE TABLE IF NOT EXISTS series ('
            'series TEXT PRIMARY KEY,'
            'title TEXT,'
            'author TEXT,'
            'category TEXT,'
            'quality INTEGER,'
            'description TEXT,'
            'correction TEXT'
        ')')
        cur.execute('CREATE TABLE IF NOT EXISTS books ('
            'id TEXT PRIMARY KEY,'
            'series TEXT,'
            'title TEXT,'
            'author TEXT'
        ')')
        cur.execute('CREATE TABLE IF NOT EXISTS files ('
            'name TEXT PRIMARY KEY,'
            'type TEXT,'
            'bookid TEXT,'
            'add_date TEXT,'
            'update_date TEXT'
        ')')
        cur.execute('CREATE TABLE IF NOT EXISTS audiobooks ('
            'id TEXT PRIMARY KEY,'
            'bookid TEXT,'
            'title TEXT,'
            'author TEXT,'
            'recorder TEXT'
        ')')
        cur.execute('CREATE TABLE IF NOT EXISTS audiofiles ('
            'filename TEXT PRIMARY KEY,'
            'abookid TEXT,'
            'chapternum INTEGER,'
            'chapter TEXT,'
            'chapterauthor TEXT,'
            'recorder TEXT,'
            'add_date TEXT'
        ')')

    def process_href(self, link):
        l = link.replace('\r', '').replace('\n', '').split('#')[0]
        if l and l[0] == '?':
            try:
                if urllib.parse.parse_qs(l[1:])['M'][0] not in 'mu':
                    return l
            except Exception:
                return l
        return None

    def process_page(self, url, realurl=None):
        r = self.session.get(realurl or urllib.parse.urljoin(self.root, url))
        r.raise_for_status()
        logging.info(url)
        date = int(time.time())
        try:
            series = parse_page(url)
        except Exception:
            series = None
        soup = bs4.BeautifulSoup(r.content, 'html5lib')
        links = []
        for a in soup.find_all('a'):
            l = self.process_href(a.get('href', ''))
            if l:
                links.append(l)
        for script in soup.find_all('script'):
            for match in re_scriptlink.finditer(script.string or ''):
                l = self.process_href(match.group(1))
                if l:
                    links.append(l)
        if series and series.startswith('audio') and series != 'audio':
            bookid, title, author, bookrecorder, audiofiles = self.process_audio(series, soup)
            return 'audio', links, (series, bookid, title, author, bookrecorder), audiofiles, url, date
        button = soup.find('input', attrs={"type": "button", "value": "線上閱讀"})
        form = button.parent if button else None
        category = None
        seriestitle = seriesauthor = None
        if form:
            script = soup.find('script', string=re.compile("SetTitle|Set.+Navigation"))
            if script:
                sc = script.string.strip()
                if 'SetTitle' in sc:
                    m = re_script.match(sc)
                    if m:
                        # author, title, category
                        seriesauthor = m.group(1)
                        seriestitle = m.group(2)
                        category = m.group(3)
                    else:
                        m = re_script2.search(sc)
                        if m:
                            category = m.group(1)
                        else:
                            logging.warning('%s: <script> not parsed: %r', url, sc)
                else:
                    m = re_script2.search(sc)
                    if m:
                        category = m.group(1)
            else:
                logging.warning('%s: <script> not found', url)
        seriesdesc = None
        books, files = [], []
        covers = []
        if form:
            author, title, bookid = None, None, None
            last_input = None
            for element in form.find_all():
                if element.name == 'font' and element.get('color') == 'CC0000':
                    if element.get('size') == '2':
                        continue
                    if author:
                        books.append((bookid, series, title, author))
                    author = (element.string or '').strip()
                    title = element.next_sibling.strip().lstrip('《【').rstrip('》】')
                elif element.name == 'input':
                    last_input = element
                    filename = None
                    function, parameter = re_onclick.match(element['onclick']).groups()
                    if function.startswith('Download'):
                        ftype = function[8:].lower()
                        if ftype == 'pdf':
                            filename = parameter + ".zip"
                        elif ftype == 'vepub':
                            filename = parameter + ".epub"
                        elif ftype.startswith('audio'):
                            filename = parameter + ".mp3"
                        elif ftype == 'jpg':
                            filename = parameter
                        else:
                            filename = parameter + "." + ftype
                            if parameter[1] != 'V':
                                # vertical
                                bookid = parameter
                    elif function.startswith('Read'):
                        bookid = parameter
                    font_date = element.next_sibling
                    add_date = upd_date = None
                    if (font_date.name == 'font' and
                        font_date.get('size') == '2'):
                        dates = re_date.findall(font_date.get_text())
                        if len(dates) > 0:
                            add_date = date_fmt(dates[0])
                        if len(dates) > 1:
                            upd_date = date_fmt(dates[1])
                    if filename:
                        files.append(
                            (filename, ftype, bookid, add_date, upd_date))
                elif element.name == 'img':
                    covers.append((element['src'], series))
            if last_input:
                element = last_input.next_sibling
                if element.name == 'font':
                    element = element.next_sibling
                desc = []
                corr = []
                while element:
                    if element.name == 'br':
                        desc.append('\n')
                    elif element.name is None:
                        desc.append(str(element).strip(' \r\n\t\x7f'))
                    elif (element.name == 'font' and element.get('size') == '2'
                          and element.find(text=re_corrtable_txt)):
                        child = element.find(text=re_corrtable_txt)
                        while child.name != 'font':
                            child = child.parent
                        element = child
                        for child in element.children:
                            if child.name == 'br':
                                corr.append('\n')
                            elif child.name == 'font':
                                corr.append(child.get_text().strip(' \r\n\t\x7f'))
                            elif child.name == 'img':
                                pass
                            elif child.name is None:
                                corr.append(child.string.strip(' \r\n\t\x7f'))
                            else:
                                corr.append(child.get_text().strip(' \r\n\t\x7f'))
                    elif element.name in ('span', 'table', 'hr'):
                        pass
                    elif (element.name == 'font' and element.get('size') == '2'):
                        pass
                    elif element.name in ('hr',):
                        break
                    elif element.name in ('b', 'i', 'font', 'a'):
                        desc.append(element.get_text().strip(' \r\n\t\x7f'))
                    element = element.next_sibling
                desc = re_newlines.sub('\n\n', ''.join(desc).strip())
                corr = re_corrtable.sub('', ''.join(corr)).strip()
                if re_quality2.search(desc):
                    quality = 2
                elif re_quality1.search(desc):
                    quality = 1
                else:
                    quality = 0
            if author:
                books.append((bookid, series, title, author))
                seriesdesc = (
                    series, seriestitle or title, seriesauthor or author,
                    category, quality, desc, corr
                )
        return 'page', links, seriesdesc, books, files, covers, url, date

    def process_audio(self, abookid, soup):
        table = soup.find('table', border='0', cellspacing='0', cellpadding='0', width="530")
        h4 = table.h4
        font = h4.find('font', color="CC0000")
        a = h4.a
        match = re_audiobooktitle.match(h4.get_text().strip())
        if font:
            author = font.string.strip()
        else:
            author = match.group(1)
        if a:
            title = a.string.strip().strip('《》【】')
            bookid = parse_page(a['href'])
        else:
            title = match.group(2)
            bookid = None
        bookrecorder = match.group(3)
        contenttable = h4.parent.table
        audiofiles = []
        filename = chapter = cnum = cauthor = recorder = add_date = None
        for td in contenttable.find_all('td'):
            if td.audio:
                filename = td.audio.source['src']
                audiofiles.append((filename, abookid, cnum, chapter, cauthor, recorder, add_date))
                filename = chapter = cnum = cauthor = recorder = add_date = None
            else:
                a = td.a
                if a:
                    cnum = int(parse_page(a['href']).split(':')[-1])
                    chapter = a.string.strip()
                    match = re_recorder.match(str(a.next_sibling).strip())
                    if match:
                        recorder = match.group(1)
                    aleftstr = a.previous_sibling
                    if isinstance(aleftstr, bs4.NavigableString):
                        cauthor = str(aleftstr).strip().rstrip('《【')
                else:
                    cnum = chapter = recorder = None
                match = re_audiobookchapter.match(td.get_text().strip())
                if not match:
                    match = re_audiobookchapter2.match(td.get_text().strip())
                if match:
                    # check real no author
                    if cauthor is None:
                        cauthor = match.group(1)
                    cauthor = cauthor or None
                    chapter = chapter or match.group(2)
                    recorder = recorder or match.group(3)
                    add_date = date_fmt(match.group(4))
        return bookid, title, author, bookrecorder, audiofiles

    def process_cover(self, url):
        r = self.session.get(urllib.parse.urljoin(self.root, url))
        if r.status_code == 404:
            img = None
        else:
            r.raise_for_status()
            img = r.content
        logging.info(url)
        if 'Last-Modified' in r.headers:
            modified = parse_date(r.headers['Last-Modified'])
        else:
            modified = int(time.time())
        return 'cover', modified, img, url

    def process_result(self, result):
        cur = self.db.cursor()
        if result[0] == 'cover':
            cur.execute('UPDATE covers SET modified=?, img=? WHERE filename=?',
                result[1:])
            return
        if result[0] == 'page':
            _, links, seriesdesc, books, files, covers, url, date = result
            if seriesdesc:
                cur.execute('REPLACE INTO series VALUES (?,?,?,?,?,?,?)', seriesdesc)
            for row in books:
                cur.execute('REPLACE INTO books VALUES (?,?,?,?)', row)
            for row in covers:
                cur.execute('INSERT OR IGNORE INTO covers VALUES (?,?,?,?)',
                            row + (None, None))
            for row in files:
                cur.execute('REPLACE INTO files VALUES (?,?,?,?,?)', row)
        elif result[0] == 'audio':
            _, links, abdesc, audiofiles, url, date = result
            cur.execute('REPLACE INTO audiobooks VALUES (?,?,?,?,?)', abdesc)
            for row in audiofiles:
                cur.execute('REPLACE INTO audiofiles VALUES (?,?,?,?,?,?,?)', row)
        cur.execute('UPDATE links SET updated=? WHERE url=?', (date, url))
        for link in links:
            cur.execute('INSERT OR IGNORE INTO links VALUES (?, ?)', (link, None))

    def get_tasks(self):
        last_time = last_tasks = None
        cur = self.db.cursor()
        yield [('/', 'page')]
        while 1:
            tasks = cur.execute(
                "SELECT * FROM ("
                "SELECT url, 'page' type FROM links WHERE updated IS NULL "
                "UNION ALL "
                "SELECT filename url, 'cover' type FROM covers "
                "  WHERE modified IS NULL "
                ") q ORDER BY RANDOM() LIMIT 100").fetchall()
            remaining = cur.execute(
                "SELECT CAST(sum(done)*100 AS REAL)/sum(total), "
                "  (sum(total) - sum(done)) "
                "FROM ("
                "  SELECT count(*) total, count(updated) done FROM links "
                "  UNION ALL "
                "  SELECT count(*) total, count(modified) done FROM covers"
                ") q"
            ).fetchone()
            if tasks:
                if last_time:
                    eta = (time.monotonic() - last_time)/last_tasks*remaining[1]
                    tmin, tsec = divmod(eta, 60)
                    thour, tmin = divmod(tmin, 60)
                    etatxt = ', ETA %02d:%02d:%02d' % (thour, tmin, tsec)
                else:
                    etatxt = ''
                logging.info('Progress %.2f%%%s' % (remaining[0], etatxt))
                last_time = time.monotonic()
                last_tasks = len(tasks)
                yield tasks
            else:
                return

    def do_fetch(self, task):
        link, ltype = task
        try:
            if ltype == 'page':
                return self.process_page(link)
            else:
                return self.process_cover(link)
        except requests.exceptions.ConnectionError as ex:
            logging.warning('ConnectionError: ' + link)
        except Exception:
            logging.exception('Failed to follow link: ' + link)

    def start(self):
        for tasks in self.get_tasks():
            for result in self.executor.map(self.do_fetch, tasks):
                if result:
                    self.process_result(result)
                    self.db.commit()

    def __del__(self):
        self.db.commit()
        self.db.close()

if __name__ == '__main__':
    hc = HaodooCrawler(sys.argv[1] if len(sys.argv) > 1 else 'haodoo.db')
    hc.init_db()
    try:
        hc.start()
    finally:
        hc.db.commit()
