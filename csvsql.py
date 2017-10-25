#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import re
import csv
import sys
import codecs
import argparse
import binascii
import collections

ESCAPE_SEQUENCE_RE = re.compile(r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''', re.UNICODE | re.VERBOSE)

re_float = re.compile(r'^(-?[0-9]*\.?[0-9]+(e[-+]?[0-9]+)?|nan|[+-]?inf)$', re.I)
re_int = re.compile(r'^(0|-?[1-9][0-9]*)$')
re_null = re.compile(r'^(|null|\\N)$', re.I)
re_null2 = re.compile(r'^( |-|\.|none|na|n/a)$', re.I)
re_null3 = re.compile(r'^(|null|\\N| |-|\.|none|na|n/a)$', re.I)
re_nonp = re.compile(r'[\000-\010\013\014\016-\037]')

# SMALLINT < INTEGER < BIGINT < DECIMAL < DOUBLE < TEXT < BLOB
# We don't detect BOOLEAN

TYPES = {v:k for k, v in enumerate((
    'SMALLINT', 'INTEGER', 'BIGINT', 'DECIMAL', 'DOUBLE', 'TEXT', 'BLOB'))}

BIGINT_MIN = -9223372036854775808
BIGINT_MAX = 9223372036854775807
INT_MIN = -2147483648
INT_MAX = 2147483647
# be conservative
SMALLINT_MIN = -128
SMALLINT_MAX = 127

class CustumDialect(csv.Dialect):
    pass

def decode_escapes(s):
    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return ESCAPE_SEQUENCE_RE.sub(decode_match, s)

def main():
    parser = argparse.ArgumentParser(description="Generate SQL definition from CSV files. Automagically determines field type.", epilog="--delimiter accepts c-style escaped string, eg. '\\t' for tabs")
    parser.add_argument("-d", "--delimeter", help="A one-character string used to separate fields, defaults to ','.", default=",", metavar="CHAR")
    parser.add_argument("-e", "--escapechar", help="The escapechar removes any special meaning from the following character.", metavar="CHAR")
    parser.add_argument("-q", "--quotechar", help="A one-character string used to quote fields containing special characters.", default='"', metavar="CHAR")
    parser.add_argument("-s", "--skipinitialspace", help="When used, whitespace immediately following the delimiter is ignored.", action='store_true')
    parser.add_argument("-t", "--strict", help="When used, exit on bad CSV input.", action='store_true')
    parser.add_argument("-D", "--no-doublequote", help="The escapechar is used as a prefix to the quotechar.", action="store_true")
    parser.add_argument("-c", "--encoding", help="CSV encoding to validate.", default='utf-8')
    parser.add_argument("-i", "--insert", help="Output inserts.", action='store_true')
    parser.add_argument("--begin", help="Command to start a transaction, defaults to BEGIN", default='BEGIN')
    parser.add_argument("-H", "--no-header", help="First row is not header.", action="store_true")
    parser.add_argument("file", help="Input file")
    args = parser.parse_args()
    dialect = CustumDialect
    dialect.delimiter = decode_escapes(args.delimeter)
    dialect.doublequote = not args.no_doublequote
    dialect.escapechar = args.escapechar
    dialect.lineterminator = '\r\n'
    dialect.quotechar = args.quotechar
    dialect.quoting = csv.QUOTE_MINIMAL
    dialect.skipinitialspace = args.skipinitialspace
    dialect.strict = args.strict
    with open(args.file, 'rb') as fb:
        f = io.TextIOWrapper(fb, encoding='latin1', newline='')
        reader = csv.reader(f, dialect)
        columns = row = next(reader)
        if args.no_header:
            columns = ('c%d' % i for i in range(len(row)))
            f.seek(0)
        header = collections.OrderedDict.fromkeys(columns)
        ids = collections.OrderedDict((x, set()) for x in header if 'id' in x.lower())
        for row in reader:
            for key, col in zip(header, row):
                coltype = header[key]
                if re_null.match(col):
                    if key in ids:
                        del ids[key]
                elif (coltype and TYPES[coltype] < TYPES['TEXT']
                      and re_null2.match(col)):
                    if key in ids:
                        del ids[key]
                elif re_int.match(col):
                    if coltype and TYPES[coltype] > TYPES['DECIMAL']:
                        continue
                    intval = int(col)
                    if intval > BIGINT_MAX or intval < BIGINT_MIN:
                        dtype = 'DECIMAL'
                    elif intval > INT_MAX or intval < INT_MIN:
                        dtype = 'BIGINT'
                    # be conservative, don't use <=
                    elif SMALLINT_MIN < intval < SMALLINT_MAX:
                        dtype = 'SMALLINT'
                    else:
                        dtype = 'INTEGER'
                    if not coltype or TYPES[coltype] < TYPES[dtype]:
                        header[key] = dtype
                    if key in ids:
                        if col in ids[key]:
                            del ids[key]
                        else:
                            ids[key].add(col)
                elif re_float.match(col):
                    if coltype and TYPES[coltype] > TYPES['DOUBLE']:
                        continue
                    elif key in ids:
                        del ids[key]
                    header[key] = 'DOUBLE'
                elif coltype != 'BLOB':
                    if key in ids:
                        del ids[key]
                    if re_nonp.search(col):
                        header[key] = 'BLOB'
                    else:
                        try:
                            col.encode('latin1').decode(args.encoding)
                            header[key] = 'TEXT'
                        except UnicodeDecodeError:
                            header[key] = 'BLOB'
        tablename = os.path.basename(os.path.splitext(fb.name)[0])
        if not tablename.isidentifier():
            tablename = '"%s"' % tablename
        pkey = tuple(ids.keys())[0] if ids else None
        result = []
        result.append('CREATE TABLE %s (' % tablename)
        for k, v in header.items():
            if v is None:
                v = header[k] = 'TEXT'
            result.append('%s %s%s,' % (
                k if k.isidentifier() else '"%s"' % k,
                v if v != 'DOUBLE' else 'DOUBLE PRECISION',
                ' PRIMARY KEY' if k == pkey else ''
            ))
        result[-1] = result[-1][:-1]
        result.append(');')
        print('\n'.join(result))
    if not args.insert:
        return
    header_idx = tuple(header.values())
    print(args.begin + ';')
    with open(args.file, 'rb') as fb:
        f = io.TextIOWrapper(fb, encoding='latin1', newline='')
        reader = csv.reader(f, dialect)
        if not args.no_header:
            next(reader)
        for row in reader:
            vals = []
            for k, v in enumerate(row):
                coltype = header_idx[k]
                if TYPES[coltype] < TYPES['TEXT']:
                    if re_null3.match(v):
                        vals.append('null')
                    else:
                        vals.append(v)
                elif coltype == 'TEXT':
                    vals.append("'%s'" % v.replace("'", "''"))
                    # .replace('\r', "'||char(13)||'").replace('\n', "'||char(10)||'"))
                else:
                    vals.append("X'%s'" % binascii.b2a_hex(v.encode('latin1')).decode('ascii'))
            print('INSERT INTO %s VALUES (%s);' % (
                tablename, ','.join(vals)))
    print('COMMIT;')

if __name__ == '__main__':
    main()
