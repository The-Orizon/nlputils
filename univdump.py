#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import collections

'''
This script tries its best to fvck these various esoteric hard-to-process
user database dump or leak files.
'''

re_field = re.compile(r'(<\w+>)')

RecFormat = collections.namedtuple('RecFormat', ('regex', 'fields'))

FORMATS = (
'<password>',
'<email>,<password>',
'<email>\t<password>',
'<email>----<password>',
'<email> <password>',
'<email>    <password>',
'<username>\t<password>\t<email>',
'<username>\s+<md5>\s+<email>',
'<username>\t<md5>\t<email>',
'<username>\t<md5>\t<email>\t<password>',
'<username>\t<md5>\t\t\t<email>\t<password>',
'<username>\t\|\t<md5>\t\|\t<email>\t\|\t<password>',
'<email>\t<md5>\t<username>\t<email>\t<password>',
'<username>,<password>,<email>',
'<email>\t<md5>\t<name>\t<username>\t<md5>\t<phone>\t<digits>',
'<digits>\t<username>\t<md5>\t<other>\t<other>\t<digits>\t<email>\t<ignore>',
"\(<digits>,\s+'<email>',\s+'<extuname>',\s+'<md5>',\s+<digits>\),",
)

class FormatDetector:
    TEMPLATES = {
        'password': '[ -~]+',
        'email': '[A-Za-z0-9._-]+@[A-Za-z0-9.-]+',
        'username': '[\w.]+',
        'extuname': '\S+',
        'name': '[\w .]+',
        'md5': '[A-Fa-f0-9]{32}',
        'phone': '[0-9 +-]{5,}',
        'digits': '[0-9]+',
        'other': '.+?',
        'ignore': '.+',
    }
    def __init__(self, formats):
        self.formats = []

    def makeindex():
        pass

if __name__ == '__main__':
    pass
