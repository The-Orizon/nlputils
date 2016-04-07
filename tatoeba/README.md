These scripts convert [Tatoeba dumps](https://tatoeba.org/eng/downloads) into a SQLite db and raw text.

1. Download these tar.bz2 archives from https://tatoeba.org/eng/downloads (`sentences.tar.bz2` is the only **require**d, if you don't use other information)
2. Run `python3 tatoeba2db.py`
3. If you want to get raw text, run `getsingle.py` or `getparallel.py`
