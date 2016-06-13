#!/usr/bin/env python
import argparse
import hashlib
import os.path
import re
import sqlite3
import sys
import time


def parse_args():
    desc = 'Deduplicate a directory tree according to file content. Useful for scattered photos.'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('db_file', help='Hash database (sqlite3) file')
    parser.add_argument('--include', default='.*', help='Regex for files to include')
    parser.add_argument(
        '--exclude',
        default='',
        help='Regex for files to exclude. Higher precedence than include regex'
    )
    subparsers = parser.add_subparsers(help='command')

    # create #
    parser_create = subparsers.add_parser('create', help='Create hash database')
    parser_create.add_argument('target_dir', help='Target directory to start at')
    parser_create.add_argument(
        '-s', '--show',
        action='store_true',
        help='Show files that would be added to database, but don\'t modify it'
    )
    parser_create.set_defaults(func=cmd_create)

    # check #
    parser_check = subparsers.add_parser('check', help='Check file or directory against database')
    parser_check.add_argument('source', help='Source file or directory to dedup')
    parser_check.set_defaults(func=cmd_check)

    args = parser.parse_args()

    args.include = re.compile(args.include)
    args.exclude = re.compile(args.exclude)

    return args


def traverse(target_dir, include_re, exclude_re, peek=False, do_digest=True):
    """
    Walk directory tree with respect to inclusion and exclusion regular expressions.

    :param str target_dir: directory to start from
    :param SRE_Pattern include_re: compiled RE for including files
    :param SRE_Pattern exclude_re: compiled RE for excluding files
    :param bool peek: whether to just peek at files and not hash along the way
    :return: generator of 1) peek is False: (filename, digest) tuples 2) peek is True: count
    :rtype: generator
    """
    count = 0
    for dirpath, dirnames, filenames in os.walk(target_dir):
        # prune any directories if needed #
        for d in dirnames[:]:
            full_d = os.path.join(dirpath, d)
            exclude_match = exclude_re.match(full_d)
            if (exclude_match and exclude_re.pattern) or not include_re.match(full_d):
                dirnames.remove(d)

        # iterate each file #
        for f in filenames:
            full_f = unicode(os.path.join(dirpath, f), 'utf_8')

            # ignore empty files
            if os.path.getsize(full_f) == 0:
                continue

            exclude_match = exclude_re.match(full_f)
            if exclude_match and exclude_re.pattern:
                continue

            if include_re.match(full_f):
                if peek:
                    count += 1
                else:
                    if do_digest:
                        m = hashlib.md5()
                        m.update(open(full_f, 'rb').read())
                        digest = m.hexdigest()
                    else:
                        digest = None
                    yield (full_f, digest)
    if peek:
        yield count


def cmd_create(args):
    def show_progress(cur):
        sys.stdout.write('\x1b[1G{}/{}\x1b[J'.format(cur, file_count))
        sys.stdout.flush()

    if args.show:
        for i, (filename, digest) in enumerate(traverse(args.target_dir, args.include, args.exclude, do_digest=False)):
            print filename
        print
        print 'Discovered {} files'.format(i + 1)
        return

    file_count = traverse(args.target_dir, args.include, args.exclude, peek=True).next()

    conn = sqlite3.connect(args.db_file)

    cur = conn.cursor()
    cur.execute('''CREATE table hashes
    (filename text, hash text)''')
    time_before = time.time()  # hopefully system time isn't changed now

    for i, (filename, digest) in enumerate(traverse(args.target_dir, args.include, args.exclude)):
        cur.execute('INSERT INTO hashes VALUES(?, ?)', (filename, digest))
        show_progress(i + 1)

    conn.commit()
    time_after = time.time()
    conn.close()

    time_elapsed = time_after - time_before
    print
    print 'Inserted {} hashes into database in {} seconds.'.format(file_count, time_elapsed)


def cmd_check(args):
    def check_one(digest):
        res_filename = None
        cur.execute('SELECT filename FROM hashes WHERE hash=?', (digest,))
        res = cur.fetchone()
        if res:
            res_filename, = res
        return res_filename

    conn = sqlite3.connect(args.db_file)
    cur = conn.cursor()

    match_count = 0
    if os.path.isfile(args.source):
        if os.path.getsize(args.source):
            print 'Empty file: "{}"'.format(args.source)
        else:
            m = hashlib.md5()
            m.update(open(args.source, 'rb').read())

            res_filename = check_one(m.hexdigest())
            if res_filename:
                match_count += 1
                print args.source
                print '\t' + res_filename
    else:
        for filename, digest in traverse(args.source, args.include, args.exclude):
            res_filename = check_one(digest)
            if res_filename:
                match_count += 1
                print filename
                print '\t' + res_filename

    conn.close()

    print 'Found {} matches'.format(match_count)


def main(args):
    args.func(args)


if __name__ == '__main__':
    main(parse_args())
