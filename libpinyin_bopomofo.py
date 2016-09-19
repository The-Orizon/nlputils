#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Decorators around methods for potential monkey-patching -- I am tooooo
lazy to do anything else now.

License: WTFPL -- You just DO WHAT THE FUCK YOU WANT TO.
"""
from __future__ import unicode_literals
import re
STYLE_BOPOMOFO = 233

bopomofo_replace = (
    (re.compile('^m(\d)$'), 'mu\\1'),  # 呣
    (re.compile('^r5$'), 'er5'),  # 〜兒
    (re.compile('iu'), 'iou'),
    (re.compile('ui'), 'uei'),
    (re.compile('ong'), 'ung'),
    (re.compile('^yi?'), 'i'),
    (re.compile('^wu?'), 'u'),
    (re.compile('iu'), 'v'),
    (re.compile('^([jqx])u'), '\\1v'),
    (re.compile('([iuv])n'), '\\1en'),
    (re.compile('^zhi?'), 'Z'),
    (re.compile('^chi?'), 'C'),
    (re.compile('^shi?'), 'S'),
    (re.compile('^([zcsr])i'), '\\1'),
    (re.compile('ai'), 'A'),
    (re.compile('ei'), 'I'),
    (re.compile('ao'), 'O'),
    (re.compile('ou'), 'U'),
    (re.compile('ang'), 'K'),
    (re.compile('eng'), 'G'),
    (re.compile('an'), 'M'),
    (re.compile('en'), 'N'),
    (re.compile('er'), 'R'),
    (re.compile('eh'), 'E'),
    (re.compile('([iv])e'), '\\1E'),
)
bopomofo_table = str.maketrans('bpmfdtnlgkhjqxZCSrzcsiuvaoeEAIOUMNKGR2345',
    'ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦˊˇˋ˙')

def translate_bopomofo(pinyin):
    out = pinyin
    for f, r in bopomofo_replace:
        out = f.sub(r, out)
    return out.translate(bopomofo_table)

tone_num = re.compile('^([a-z]+)([0-4])([a-z]*)$')

def translate_bopomofo_tone2(syllable):
    match = tone_num.match(syllable)
    if match:
        return translate_bopomofo(match.expand(r'\1\3\2').replace('0', '5'))
    else:
        return syllable

def pinyin_bopomofo_factory(pinyin):
    def f(han, style, heteronym, errors='default'):
        if style == STYLE_BOPOMOFO:
            # FIXME: this can't cover all error handling methods
            # we should directly patch pypinyin
            return list(map(translate_bopomofo_tone2, pinyin(han, 2, heteronym, errors)))
        else:
            return pinyin(han, style, heteronym, errors)
    return f
