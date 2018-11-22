#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import time
import sqlite3
import logging
import requests
import urllib.parse
import concurrent.futures
from bs4 import BeautifulSoup

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-TW,zh;q=0.8,zh-CN;q=0.6,en;q=0.4",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36",
}

logging.basicConfig(stream=sys.stderr, format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

re_title = re.compile('(.+?)[【《](.+)[》】]')
re_script = re.compile(r'SetTitle\("(.+?)[【《](.+)[》】]"\).+\nSetLink\(\'<a href=.+>(\w+)( +書目)?</a>\'\)')
re_script2 = re.compile(r'(\w+) +書目')
re_scriptlink = re.compile(r'<a href="([^"]+)">.+?</a>')
re_onclick = re.compile(r"(\w+)\('([^']+)'.*\)")
re_date = re.compile('\d{4}/\d{1,2}/\d{1,2}')

date_fmt = lambda s: '%04d-%02d-%02d' % tuple(map(int, s.split('/')))

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
        cur.execute('CREATE TABLE IF NOT EXISTS books ('
            'id TEXT PRIMARY KEY,'
            'series TEXT,'
            'title TEXT,'
            'author TEXT,'
            'category TEXT'
        ')')
        cur.execute('CREATE TABLE IF NOT EXISTS files ('
            'name TEXT PRIMARY KEY,'
            'type TEXT,'
            'bookid TEXT,'
            'add_date TEXT,'
            'update_date TEXT'
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
            series = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)['P'][0]
        except Exception:
            series = None
        soup = BeautifulSoup(r.content, 'html5lib')
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
        button = soup.find('input', attrs={"type": "button", "value": "線上閱讀"})
        form = button.parent if button else None
        category = None
        if form:
            script = soup.find('script', string=re.compile("SetTitle|Set.+Navigation"))
            if script:
                sc = script.string.strip()
                if 'SetTitle' in sc:
                    m = re_script.match(sc)
                    if m:
                        # author, title, category
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
        books, files = [], []
        if form:
            author, title, bookid = None, None, None
            for element in form.find_all():
                if element.name == 'font' and element.get('color') == 'CC0000':
                    if element.get('size') == '2':
                        continue
                    if author:
                        books.append((bookid, series, title, author, category))
                    author = (element.string or '').strip()
                    title = element.next_sibling.strip().lstrip('《【').rstrip('》】')
                elif element.name == 'input':
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
            if author:
                books.append((bookid, series, title, author, category))
        return links, books, files, url, date

    def process_result(self, links, books, files, url, date):
        cur = self.db.cursor()
        cur.execute('REPLACE INTO links VALUES (?, ?)', (url, date))
        for link in links:
            cur.execute('INSERT OR IGNORE INTO links VALUES (?, ?)', (link, None))
        for row in books:
            cur.execute('REPLACE INTO books VALUES (?,?,?,?,?)', row)
        for row in files:
            cur.execute('REPLACE INTO files VALUES (?,?,?,?,?)', row)

    def get_tasks(self):
        last_time = last_tasks = None
        cur = self.db.cursor()
        yield ['/']
        while 1:
            tasks = list(x[0] for x in cur.execute('SELECT url FROM links WHERE updated IS NULL ORDER BY RANDOM() LIMIT 100'))
            remaining = cur.execute("SELECT CAST(count(updated)*100 AS REAL)/count(*), (count(*) - count(updated)) FROM links").fetchone()
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

    def do_fetch(self, link):
        try:
            return self.process_page(link)
        except requests.exceptions.ConnectionError as ex:
            logging.warning('ConnectionError: ' + link)
        except Exception:
            logging.exception('Failed to follow link: ' + link)

    def start(self):
        cur = self.db.cursor()
        for tasks in self.get_tasks():
            for result in self.executor.map(self.do_fetch, tasks):
                if result:
                    self.process_result(*result)
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
