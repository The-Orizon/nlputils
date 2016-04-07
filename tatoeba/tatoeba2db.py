#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Convert Tatoeba dumps (https://tatoeba.org/eng/downloads) into a SQLite db.

Copyright (c) 2016 gumblex

This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.
'''

import os
import io
import sys
import time
import tarfile
import sqlite3
import calendar

cint = lambda s: None if s == '\\N' else int(s)
cdate = lambda s: None if s in ('\\N', '0000-00-00 00:00:00') else calendar.timegm(time.strptime(s, '%Y-%m-%d %H:%M:%S'))

def stream_tarfile(filename):
    with tarfile.open(filename, 'r') as tf:
        f = tf.extractfile(tf.next())
        yield from io.TextIOWrapper(f, 'utf-8', newline='\n')

print('Creating schema')
db = sqlite3.connect('tatoeba.db')
cur = db.cursor()
cur.execute(
    'CREATE TABLE IF NOT EXISTS sentences ('
    'id INTEGER PRIMARY KEY,'
    'lang TEXT,'
    'text TEXT,'
    'username TEXT,'
    'date_added INTEGER,'
    'date_modified INTEGER,'
    'audio INTEGER'
')')
cur.execute(
    'CREATE TABLE IF NOT EXISTS links ('
    'sentence INTEGER,'
    'translation INTEGER,'
    'FOREIGN KEY(sentence) REFERENCES sentences(id),'
    'FOREIGN KEY(translation) REFERENCES sentences(id)'
')')
cur.execute(
    'CREATE TABLE IF NOT EXISTS tags ('
    'sentence INTEGER,'
    'tag TEXT,'
    'FOREIGN KEY(sentence) REFERENCES sentences(id)'
')')
cur.execute(
    'CREATE TABLE IF NOT EXISTS user_lists ('
    'id INTEGER PRIMARY KEY,'
    'username TEXT,'
    'date_created INTEGER,'
    'date_modified INTEGER,'
    'list_name TEXT,'
    'editable TEXT'
')')
cur.execute(
    'CREATE TABLE IF NOT EXISTS sentences_in_lists ('
    'list INTEGER,'
    'sentence INTEGER,'
    'FOREIGN KEY(list) REFERENCES user_lists(id),'
    'FOREIGN KEY(sentence) REFERENCES sentences(id)'
')')
cur.execute(
    'CREATE TABLE IF NOT EXISTS jpn_indices ('
    'sentence INTEGER,'
    'meaning INTEGER,'
    'text TEXT,'
    'FOREIGN KEY(sentence) REFERENCES sentences(id),'
    'FOREIGN KEY(meaning) REFERENCES sentences(id)'
')')
cur.execute(
    'CREATE TABLE IF NOT EXISTS user_languages ('
    'lang TEXT,'
    'skill INTEGER,'
    'username TEXT,'
    'details TEXT'
')')
cur.execute(
    'CREATE TABLE IF NOT EXISTS users_sentences ('
    'username TEXT,'
    # 'lang TEXT,'
    'sentence INTEGER,'
    'rating INTEGER,'
    'date_added INTEGER,'
    'date_modified INTEGER,'
    'FOREIGN KEY(sentence) REFERENCES sentences(id)'
')')
db.commit()

if os.path.isfile('sentences_detailed.tar.bz2'):
    print('Importing sentences_detailed.tar.bz2')
    for ln in stream_tarfile('sentences_detailed.tar.bz2'):
        l = ln.rstrip('\n').split('\t')
        cur.execute('REPLACE INTO sentences (id, lang, text, username, date_added, date_modified, audio) VALUES (?, ?, ?, ?, ?, ?, 0)', (int(l[0]), l[1], l[2], l[3], cdate(l[4]), cdate(l[5])))
    db.commit()
elif os.path.isfile('sentences.tar.bz2'):
    print('sentences_detailed.tar.bz2 not found.')
    print('Importing sentences.tar.bz2')
    for ln in stream_tarfile('sentences.tar.bz2'):
        l = ln.rstrip('\n').split('\t')
        cur.execute('INSERT OR IGNORE INTO sentences (id, lang, text, audio) VALUES (?, ?, ?, 0)', (int(l[0]), l[1], l[2]))
    db.commit()
else:
    print('sentences_detailed.tar.bz2 or sentences.tar.bz2 not found.')
    sys.exit(1)
if os.path.isfile('links.tar.bz2'):
    print('Importing links.tar.bz2')
    for ln in stream_tarfile('links.tar.bz2'):
        l = ln.rstrip('\n').split('\t')
        cur.execute('REPLACE INTO links VALUES (?, ?)', (int(l[0]), int(l[1])))
    db.commit()
if os.path.isfile('tags.tar.bz2'):
    print('Importing tags.tar.bz2')
    for ln in stream_tarfile('tags.tar.bz2'):
        l = ln.rstrip('\n').split('\t')
        cur.execute('REPLACE INTO tags VALUES (?, ?)', (int(l[0]), l[1]))
    db.commit()
if os.path.isfile('user_lists.tar.bz2'):
    print('Importing user_lists.tar.bz2')
    for ln in stream_tarfile('user_lists.tar.bz2'):
        l = ln.rstrip('\n').split('\t')
        cur.execute('REPLACE INTO user_lists VALUES (?, ?, ?, ?, ?, ?)', (int(l[0]), l[1], cdate(l[2]), cdate(l[3]), l[4], l[5]))
    db.commit()
if os.path.isfile('sentences_in_lists.tar.bz2'):
    print('Importing sentences_in_lists.tar.bz2')
    for ln in stream_tarfile('sentences_in_lists.tar.bz2'):
        l = ln.rstrip('\n').split('\t')
        cur.execute('REPLACE INTO sentences_in_lists VALUES (?, ?)', (int(l[0]), int(l[1])))
    db.commit()
if os.path.isfile('jpn_indices.tar.bz2'):
    print('Importing jpn_indices.tar.bz2')
    for ln in stream_tarfile('jpn_indices.tar.bz2'):
        l = ln.rstrip('\n').split('\t')
        cur.execute('REPLACE INTO jpn_indices VALUES (?, ?, ?)', (int(l[0]), int(l[1]), l[2]))
    db.commit()
if os.path.isfile('sentences_with_audio.tar.bz2'):
    print('Importing sentences_with_audio.tar.bz2')
    for ln in stream_tarfile('sentences_with_audio.tar.bz2'):
        cur.execute('UPDATE OR IGNORE sentences SET audio = 1 WHERE id = ?', (int(ln.strip()),))
    db.commit()
if os.path.isfile('user_languages.tar.bz2'):
    print('Importing user_languages.tar.bz2')
    last_line = last_detail = None
    for ln in stream_tarfile('user_languages.tar.bz2'):
        ln = ln.rstrip('\n')
        if ln.endswith('\\'):
            if last_detail:
                last_detail += ln[:-1] + '\n'
            else:
                l = ln.split('\t')
                last_line = (l[0], cint(l[1]), l[2])
                last_detail = l[-1][:-1] + '\n'
        elif last_detail:
            cur.execute('REPLACE INTO user_languages VALUES (?, ?, ?, ?)', last_line + (last_detail + ln,))
            last_line = last_detail = None
        else:
            l = ln.split('\t')
            cur.execute('REPLACE INTO user_languages VALUES (?, ?, ?, ?)', (l[0], cint(l[1]), l[2], l[3]))
    if last_detail:
        cur.execute('REPLACE INTO user_languages VALUES (?, ?, ?, ?)', last_line + (last_detail,))
    db.commit()
if os.path.isfile('users_sentences.csv'):
    print('Importing users_sentences.csv')
    with open('users_sentences.csv', 'r', encoding='utf-8') as f:
        for ln in f:
            l = ln.rstrip('\n').split('\t')
            cur.execute('REPLACE INTO users_sentences VALUES (?, ?, ?, ?, ?)', (l[0], int(l[1]), int(l[2]), cdate(l[3]), cdate(l[4])))
    db.commit()
cur.execute('VACUUM')
print('Done.')
