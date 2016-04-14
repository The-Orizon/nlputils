#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import hashlib
import collections
import multiprocessing

'''
This script tries to fvck these various esoteric hard-to-process
user database dump or leak files.

Format: username <TAB> email <TAB> password <TAB> md5
'''

md5hash = lambda s: hashlib.md5(s.encode('utf-8')).hexdigest()

seperators = ('\t', '----', '|', ',', None)

re_ctrl = re.compile("[\x00-\x08\x0A-\x1F]+")
remove_str = (
    u"用户组&emsp;:<span class='gray'>平民 (-1)",
    u"<tr><td>用户IP&emsp;:<span class=gray>"
)

re_whitespace = re.compile('[\t ]+')
re_password = re.compile('^[ -~]{6,64}$')
re_username_ext = re.compile(r'^\S{2,64}$', re.U)

re_formats = collections.OrderedDict((
    ('email', re.compile('^[A-Za-z0-9._-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]{2,}$')),
    ('md5', re.compile('^[A-Fa-f0-9]{32}$')),
    ('username', re.compile(r'^[\w.]{2,64}$')),
    ('password', re_password),
    (None, None) # catch all username/nickname
))

def sanitize(s):
    s = re_ctrl.sub('', s.strip())
    try:
        s = s.decode('utf-8')
    except UnicodeDecodeError:
        s = s.decode('gbk', 'ignore')
    for rm in remove_str:
        s = s.replace(rm, '')
    return s

def try_formats(s):
    if not s:
        return
    for sep in seperators:
        if sep:
            fields = filter(None, s.split(sep))
        else:
            fields = filter(None, re_whitespace.split(s))
        if len(fields) < 2:
            continue
        for f in fields:
            fields_got = {}
            flist = re_formats.copy()
            for f in fields:
                for ftype, regex in flist.items():
                    if ftype:
                        if ftype != 'password':
                            f = f.strip()
                        if regex.match(f):
                            fields_got[ftype] = f
                            break
                    elif re_username_ext.match(f):
                        fields_got['username'] = f
                        break
                else:
                    continue
                del flist[ftype]
                if ftype is None:
                    try:
                        del flist['username']
                    except KeyError:
                        pass
                elif ftype == 'username':
                    try:
                        del flist[None]
                    except KeyError:
                        pass
            return fields_got
    else:
        if re_password.match(s):
            return {'password': s}

def process_result(r):
    password = r.get('password', '')
    md5 = r.get('md5', '').lower()
    username = r.get('username', '').strip()
    email = r.get('email', '').lstrip('-')
    if password and md5:
        if md5hash(password) == md5:
            md5 = ''
        else:
            password = ''
    elif username and not password and re_password.match(username):
        password = username
        username = ''
    return (username, email, password, md5)

def process_line(l):
    r = try_formats(sanitize(l))
    if r:
        return u'\t'.join(process_result(r)).encode('utf-8')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '-1':
        func = map
    else:
        pool = multiprocessing.Pool()
        func = lambda fn, it: pool.imap_unordered(fn, it, 256)
    for result in func(process_line, sys.stdin):
        if result:
            print(result)
