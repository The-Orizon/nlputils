#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import time
import sqlite3
import logging
import requests
import urllib.parse
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

class HaodooCrawler:

    root = 'http://www.haodoo.net/'

    def __init__(self, db='haodoo.db'):
        self.db = sqlite3.connect(db)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

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
            'bookid TEXT'
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
        date = int(time.time())
        try:
            series = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)['P'][0]
        except Exception:
            series = None
        soup = BeautifulSoup(r.content, 'lxml')
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
                    if filename:
                        files.append((filename, ftype, bookid))
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
            cur.execute('REPLACE INTO files VALUES (?,?,?)', row)

    def get_task(self):
        cur = self.db.cursor()
        result = cur.execute('SELECT url FROM links WHERE updated IS NULL ORDER BY RANDOM() LIMIT 1').fetchone()
        if result:
            return result[0]

    def start(self):
        cur = self.db.cursor()
        if cur.execute('SELECT 1 FROM links LIMIT 1').fetchone():
            link = self.get_task()
        else:
            link = '/'
        while link:
            logging.info(link)
            try:
                self.process_result(*self.process_page(link))
            except requests.exceptions.ConnectionError as ex:
                logging.warning(ex)
            except Exception:
                logging.exception('Failed to follow a link.')
            link = self.get_task()

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
