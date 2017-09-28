#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import jieba

_get_module_path = lambda path: os.path.normpath(os.path.join(os.getcwd(),
                                                              os.path.dirname(__file__), path))
_get_abs_path = lambda path: os.path.normpath(os.path.join(os.getcwd(), path))

dt = jieba.Tokenizer()

dt.cache_file = "jiebazhc.cache"

if os.path.isfile(_get_module_path("dict.txt")):
    dt.set_dictionary(_get_module_path("dict.txt"))
elif os.path.isfile(_get_abs_path("dict.txt")):
    dt.set_dictionary(_get_abs_path("dict.txt"))

FREQ = dt.FREQ
add_word = dt.add_word
calc = dt.calc
cut = dt.cut
lcut = dt.lcut
cut_for_search = dt.cut_for_search
lcut_for_search = dt.lcut_for_search
del_word = dt.del_word
get_DAG = dt.get_DAG
initialize = dt.initialize
load_userdict = dt.load_userdict
set_dictionary = dt.set_dictionary
suggest_freq = dt.suggest_freq
tokenize = dt.tokenize
user_word_tag_tab = dt.user_word_tag_tab
