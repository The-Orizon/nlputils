# nlputils
Utility scripts or libraries for various Natural Language Processing tasks.

## List

* `charfreq.awk`: calculate character frequency.
* `convcat.py`: cat files with different encodings together.
* `csvcol.py`: get specified columns of csv files.
* `csvsql.py`: convert csv file to sql definition.
* `dbsort.tcl`: sort SQLite tables in place.
* `detokenizer.py`: detokenize Chinese text.
* `dump2db.py`: make a database from leaked password dumps.
* `epubzhconv.py`: Chinese varient conversion for epub books.
* `filtermd5.py`: remove md5s not in known list.
* `findbadlines.py`: find encoding errors in stdin.
* `gbk_pua.py`: convert PUA codes in GBK to unicode.
* `getautodesk.py`: get Moses format parallel text from [Autodesk](https://autodesk.box.com/Autodesk-PostEditing) corpus.
* `gettxtcollection.py`: merge a txt file collection to one large corpus.
* `haodoo`: crawl and download all books from [haodoo.net](http://haodoo.net).
* `iconv.py`: implements iconv.
* `iso639.json`, `iso639-to-calibre.py`: get ISO639 codes from Wikipedia and convert to calibre po file.
* `jiebazhc`: tokenize Classical Chinese using [jieba](https://github.com/fxsjy/jieba).
* `libpinyin_bopomofo.py`: Decorator to use with [python-pinyin](https://github.com/mozillazg/python-pinyin), to convert Pinyin to Bopomofo. (now useless)
* `ngramfreq.awk`: calculate n-gram character frequency.
* `num2chinese.py`: convert numbers to Chinese numbers.
* `phrasecombine.py`: combine splitted words to large phrases given a dictionary.
* `pwdsort.js`, `zxcvbn.js`: print out password strength according to [zxcvbn](https://github.com/dropbox/zxcvbn).
* `rmdup.c`: remove duplicate lines without sort (compile with `make`, needs `libxxhash-dev`).
* `simpdump.py`: try to find username, email, password and hash from leaked password dumps.
* `splitrecutfilter.py`: reads stdin, filters non-chinese sentences and cuts sentences and words.
* `tatoeba`: convert [tatoeba](https://tatoeba.org/) dumps to a SQLite3 database.
* `wordfreq.awk`: calculate word frequency.
* `WWStarClone.py`: clone of WWStar, an ancient Classical Chinese translator.
* `zhutil.py`: misc. utils for processing Chinese.
* `modelzh.json`: model to detect Classical/Modern Chinese.


## License
If not otherwise noted in file, all files are licensed under MIT License.
