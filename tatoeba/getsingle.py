#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Get single corpus text from converted Tatoeba SQLite database.

Copyright (c) 2016 gumblex

This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.
'''

import sys
import sqlite3

def main(src):
    db = sqlite3.connect('tatoeba.db')
    cur = db.cursor()
    print(src)
    with open('tatoeba.' + src, 'w', encoding='utf-8') as w:
        for s in cur.execute('SELECT text FROM sentences WHERE lang = ?', (src,)):
            w.write(s[0].strip() + '\n')

if __name__ == '__main__':
    main(sys.argv[1])
