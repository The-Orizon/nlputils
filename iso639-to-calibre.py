#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import collections

import zhconv
import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://en.wikipedia.org/wiki/ISO_639'
HEADERS = '639-1 639-2B Scope/Type Family Native eng fra spa zho rus deu'.split(' ')

def parse_page(content):
    soup = BeautifulSoup(content, 'html5lib')
    table = soup.find('table', class_='wikitable sortable')
    languages = {}
    for tr in table.find_all('tr'):
        if not tr.td:
            continue
        name = tuple(tr.th.find_all('span'))[-1]['id']
        attr = {}
        for k, td in enumerate(tr.find_all('td')):
            if td.string:
                attr[HEADERS[k]] = td.string
        if name and attr:
            languages[name] = attr
        else:
            print(name)
    return languages

def get_all_codes():
    languages = {}
    session = requests.session()
    for i in range(26):
        ch = chr(ord('a') + i)
        url = '%s:%s' % (BASE_URL, ch)
        req = session.get(url)
        languages.update(parse_page(req.content))
        print(url)
    return languages

def calibre_iso639_po(fin, fout, target, languages, replace=True):
    # http://www-01.sil.org/iso639-3/iso-639-3_Name_Index.tab
    with open(fin, 'r', encoding='utf-8') as f1, open(fout, 'w', encoding='utf-8') as f2:
        current = None
        msgid = None
        for line in f1:
            ln = line.strip()
            if (not ln or line.startswith('# ') or ln.startswith('"')):
                f2.write(line)
            elif ln.startswith('#. '):
                current = ln[-3:]
                f2.write(line)
            elif ln.startswith('msgid'):
                msgid = line
            elif current and current in languages and ln.startswith('msgstr'):
                msgstr = ln[8:-1]
                msgstr_new = zhconv.convert(languages[current].get(target, ''), 'zh-hans')
                if msgstr_new and (replace or not msgstr):
                    diff = ''
                    if '' != msgstr != msgstr_new:
                        diff = '%s Old: %s - New: %s' % (current, msgstr, msgstr_new)
                        print(diff)
                        f2.write('# %s\n' % diff)
                    if diff or ';' in msgid or ';' in msgstr or ';' in msgstr_new:
                        f2.write('#, fuzzy\n')
                    f2.write(msgid)
                    f2.write('msgstr "%s"\n' % msgstr_new)
                else:
                    if msgstr and (';' in msgid or ';' in msgstr):
                        f2.write('#, fuzzy\n')
                    f2.write(msgid)
                    f2.write(line)
            else:
                f2.write(line)

if 0:
    languages = get_all_codes()
    with open('iso639.json', 'w') as f:
        json.dump(languages, f, sort_keys=True, indent=1)
else:
    languages = json.load(open('iso639.json'))
    calibre_iso639_po(sys.argv[1], sys.argv[2], sys.argv[3], languages)
