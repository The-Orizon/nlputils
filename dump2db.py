#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
import hashlib
import binascii

db = sqlite3.connect('leaks.db')
cur = db.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS records ('
    'username TEXT,'
    'email TEXT,'
    'password TEXT,'
    'md5 BLOB'
')')
cur.execute('CREATE INDEX IF NOT EXISTS md5_index ON records (md5)')

def update_records(stream, debug=False):
    for ln in stream:
        try:
            fields = ln.rstrip(b'\n').decode('utf-8', errors='ignore').split('\t')
            if not any(fields):
                continue
            username = fields[0].strip()
            email = fields[1].strip()
            password = fields[2]
            md5 = binascii.a2b_hex(fields[3])
            if not debug:
                cur.execute('INSERT INTO records VALUES (?,?,?,?)',
                            (username, email, password, md5))
        except Exception as ex:
            print(repr(ex), repr(ln))

def update_md5(stream):
    md5s = set()
    for row in cur.execute('SELECT DISTINCT md5 FROM records WHERE md5 IS NOT NULL'):
        md5s.add(row[0])
    for ln in stream:
        ln = ln.rstrip(b'\n')
        md5 = hashlib.md5(ln).digest()
        if md5 in md5s:
            cur.execute('UPDATE records SET password=?, md5=? WHERE md5=?',
                        (ln, b'', md5))

def vacuum():
    cur.execute('DELETE FROM records WHERE rowid NOT IN (SELECT MIN(RowId) FROM records GROUP BY username, email, password, md5)')
    cur.execute('VACUUM')

try:
    if len(sys.argv) > 1:
        if sys.argv[1] == '-p':
            update_md5(sys.stdin.buffer)
        elif sys.argv[1] == '-v':
            vacuum()
        elif sys.argv[1] == '-d':
            update_records(sys.stdin.buffer, debug=True)
        else:
            print('unrecognized arguments')
    else:
        update_records(sys.stdin.buffer)
finally:
    db.commit()
