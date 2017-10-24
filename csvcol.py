#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import io
import csv
import sys
import codecs
import argparse
import operator

ESCAPE_SEQUENCE_RE = re.compile(r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''', re.UNICODE | re.VERBOSE)

class CustumDialect(csv.Dialect):
    pass

def decode_escapes(s):
    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return ESCAPE_SEQUENCE_RE.sub(decode_match, s)

QUOTING = {
    'all': csv.QUOTE_ALL,
    'minimal': csv.QUOTE_MINIMAL,
    'nonnumeric': csv.QUOTE_NONNUMERIC,
    'none': csv.QUOTE_NONE
}

def fieldgetter(fielddef):
    out = []
    fields = fielddef.split(',')
    for field in fields:
        frange = field.split('-')
        if len(frange) == 1:
            i = int(frange[0]) - 1
            if i == -1:
                raise ValueError('field number is from 1')
            out.append(i)
        elif len(frange) == 2:
            i1 = int(frange[0]) - 1
            i2 = int(frange[1])
            if i1 == -1 or i2 == 0:
                raise ValueError('field number is from 1')
            out.extend(range(i1, i2))
        else:
            raise ValueError('invalid field definition')
    if len(out) == 1:
        return lambda x: (x[out[0]],)
    else:
        return operator.itemgetter(*out)

def main():
    parser = argparse.ArgumentParser(description="Get columns from csv files.", epilog="--delimiter and --lineterminator accepts c-style escaped string, eg. '\\t' for tabs")
    parser.add_argument("-d", "--delimeter", help="A one-character string used to separate fields, defaults to ','.", default=",", metavar="CHAR")
    parser.add_argument("-od", "--out-delimeter", help="Output delimeter, defaults to --delimeter", metavar="CHAR")
    parser.add_argument("-e", "--escapechar", help="The escapechar removes any special meaning from the following character.", metavar="CHAR")
    parser.add_argument("-oe", "--out-escapechar", help="Output escapechar, defaults to --escapechar.", metavar="CHAR")
    parser.add_argument("-l", "-ol", "--lineterminator", help="The string used to terminate lines when writing. Can be '\r', '\n' or '\r\n'.", default='\r\n', metavar="CHAR")
    parser.add_argument("-q", "--quotechar", help="A one-character string used to quote fields containing special characters.", default='"', metavar="CHAR")
    parser.add_argument("-oq", "--out-quotechar", help="Output quotechar, defaults to --quotechar.", metavar="CHAR")
    parser.add_argument("-Q", "-oQ", "--quoting", help="Output quoting mode: all, minimal, nonnumeric, none, text. Defaults to minimal, 'text' is no quoting and no errors at all.", default='minimal', choices=('all', 'minimal', 'nonnumeric', 'none', 'text'))
    parser.add_argument("-s", "--skipinitialspace", help="When used, whitespace immediately following the delimiter is ignored.", action='store_true')
    parser.add_argument("-t", "--strict", help="When used, exit on bad CSV input.", action='store_true')
    parser.add_argument("-D", "--no-doublequote", help="The escapechar is used as a prefix to the quotechar.", action="store_true")
    parser.add_argument("-oD", "--out-no-doublequote", help="Set --no-doublequote for output.", action="store_true")
    parser.add_argument("-H", "--remove-header", help="Remove first row.", action="store_true")
    parser.add_argument("fields", help="Input fields, eg. 1,2,3-5,7")
    parser.add_argument("file", help="Input files", nargs='*')
    args = parser.parse_args()
    dialect = CustumDialect
    dialect.delimiter = decode_escapes(args.delimeter)
    dialect.doublequote = not args.no_doublequote
    dialect.escapechar = args.escapechar
    dialect.lineterminator = decode_escapes(args.lineterminator)
    dialect.quotechar = args.quotechar
    dialect.quoting = csv.QUOTE_MINIMAL
    dialect.skipinitialspace = args.skipinitialspace
    dialect.strict = args.strict
    out_override = {k:v for k, v in {
        'delimiter': args.out_delimeter and decode_escapes(args.out_delimeter),
        'doublequote': not args.out_no_doublequote,
        'escapechar': args.out_escapechar,
        'lineterminator': dialect.lineterminator,
        'quotechar': args.out_quotechar
    }.items() if v is not None}
    fg = fieldgetter(args.fields)
    if args.quoting != 'text':
        writer = csv.writer(
            io.TextIOWrapper(sys.stdout.buffer, encoding='latin1'),
            dialect, quoting=QUOTING[args.quoting], **out_override)
    else:
        out_delimeter = out_override.get('delimiter', dialect.delimiter).encode('latin1')
        out_lineterminator = out_override.get('lineterminator', dialect.lineterminator).encode('latin1')
    for filename in (args.file or ['-']):
        with (open(filename, 'rb') if filename != '-'
              else sys.stdin.buffer) as fb:
            f = io.TextIOWrapper(fb, encoding='latin1', newline='')
            reader = csv.reader(f, dialect)
            if args.remove_header:
                next(reader)
            if args.quoting == 'text':
                for row in reader:
                    sys.stdout.buffer.write(out_delimeter.join(fg(row)) + out_lineterminator)
            else:
                for row in reader:
                    writer.writerow(fg(row))

if __name__ == '__main__':
    main()
