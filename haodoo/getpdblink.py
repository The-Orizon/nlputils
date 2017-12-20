#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import sqlite3
import itertools

preference = {v:k for k,v in enumerate(('updb', 'pdb', 'epub', 'mobi', 'vepub', 'prc'))}

def main(filename, update=None):
    db = sqlite3.connect(filename)
    cur = db.cursor()
    for bookid, group in itertools.groupby(cur.execute(
        "SELECT * FROM files "
        "WHERE julianday(coalesce(update_date, add_date, '9999-01-01')) "
        " >= julianday(?) ORDER BY bookid, type", (update or '0001-01-01',)),
        key=lambda x: x[2]):
        files = sorted(group, key=lambda x: preference.get(x[1], 100))
        print('http://www.haodoo.net/?M=d&P=' + files[0][0])

if __name__ == '__main__':
    filename = 'haodoo.db'
    update = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    if len(sys.argv) > 2:
        update = sys.argv[2]
    main(filename, update)
