#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Get parallel corpus in Moses-style text from converted Tatoeba SQLite database.

Copyright (c) 2016 gumblex

This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.
'''

import sys
import sqlite3

def main(src, tgt):
    db = sqlite3.connect('tatoeba.db')
    cur = db.cursor()
    print(src, tgt)
    with open('tatoeba.' + src, 'w', encoding='utf-8') as w1, open('tatoeba.' + tgt, 'w', encoding='utf-8') as w2:
        for s, t in cur.execute('SELECT s.text, t.text FROM links INNER JOIN sentences AS s ON links.sentence = s.id INNER JOIN sentences AS t ON links.translation = t.id WHERE s.lang = ? AND t.lang = ?', (src, tgt)):
            w1.write(s.strip() + '\n')
            w2.write(t.strip() + '\n')

if __name__ == '__main__':
    main(*sys.argv[1:])
