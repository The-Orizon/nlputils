#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import collections
import multiprocessing

'''
This script tries to fvck these various esoteric hard-to-process
user database dump or leak files.
'''

#Fields = collections.namedtuple('Fields', ('username', 'email', 'password', 'md5'))

seperators = ('----', '\t|\t', '\t', '|', ',', None)

templates = (
('password',),
('email', 'password'),
('username', 'password'),
('username', 'password', 'email'),
('username', 'md5', 'email'),
('username', 'md5', 'password'),
('username', 'md5', 'email', 'password'),
('username', 'email', 'md5', 'password'),
)

templates_index = collections.defaultdict(list)
for t in templates:
    templates_index[len(t)].append(t)

re_ctrl = re.compile("[\000-\037]+")
remove_str = (
    "用户组&emsp;:<span class='gray'>平民 (-1)",
    "<tr><td>用户IP&emsp;:<span class=gray>"
)

re_formats = collections.OrderedDict((
    ('email', re.compile('^[A-Za-z0-9._-]+@[A-Za-z0-9.-]+$')),
    ('md5', re.compile('^[A-Fa-f0-9]{32}$')),
    ('username', re.compile(r'^[\w.]+$')),
    ('password', re.compile('^[ -~]+$')),
    ('username_ext', re.compile(r"^\S+$", re.U))
))

def sanitize(s):
    s = re_ctrl.sub('', s.strip())
    for rm in remove_str:
        s = s.replace(rm, '')
    try:
        return s.decode('utf-8')
    except UnicodeDecodeError:
        return s.decode('gbk', 'ignore')

def try_formats(s):
    print(s.encode('utf-8'))
    for sep in seperators:
        fields = tuple(filter(None, s.split(sep)))
        if len(fields) < 2:
            continue
        print(fields)
        try:
            less_match = None
            for tmpl in templates_index[len(fields)]:
                fields_match = ['']*4
                for k, f in enumerate(fields):
                    if re_formats[tmpl[k]].match(f):
                        fields_match[k] = f
                if all(fields_match):
                    return dict(zip(tmpl, fields_match))
                elif fields_match:
                    if (not less_match or
                        sum(map(bool, fields_match)) > sum(map(bool, less_match))):
                        less_match = fields_match
            else:
                if less_match:
                    return dict(zip(tmpl, less_match))
        except KeyError:
            fields_got = {}
            flist = list(re_formats.items())
            for f in fields:
                for k, (ftype, regex) in enumerate(flist):
                    if regex.match(f):
                        fields_got[ftype] = f
                        break
                else:
                    continue
                del flist[k]
            return fields_got
    else:
        if re_formats['password'].match(s):
            return {'password': s}

def process_line(l):
    r = try_formats(sanitize(l))
    print(r)
    if r:
        print('\t'.join((r.get('username', ''), r.get('email', ''),
              r.get('password', ''), r.get('md5', ''))).encode('utf-8'))

if __name__ == '__main__':
    #pool = multiprocessing.Pool(1)
    #func = pool.imap_unordered
    func = map
    for _ in func(process_line, sys.stdin):
        pass
