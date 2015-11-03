#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: decrypt-db.py
# Author: Yuxin Wu <ppwwyyxx@gmail.com>

from argparse import ArgumentParser
from pysqlcipher import dbapi2 as sqlite

from hashlib import md5
import sys
import os

def get_args():
    parser = ArgumentParser()
    parser.add_argument('db', help='path to EnMicroMsg.db')
    parser.add_argument('imei', help='15 digit IMEI of your phone')
    parser.add_argument('uin', help='WeChat UIN')
    parser.add_argument('--output', help='output decrypted database',
                        default='decrypted.db')
    args = parser.parse_args()
    return args

def get_key(imei, uin):
    a = md5(imei + uin)
    return a.hexdigest()[:7]

if __name__ == '__main__':
    args = get_args()

    output = args.output
    if os.path.isfile(output):
        print "{} already exists. Remove? (y/n)".format(args.output),
        ans = raw_input()
        if ans not in ['y', 'Y']:
            print "Bye!"
            sys.exit()
        os.unlink(argsos.output)
    key = get_key(args.imei, args.uin)
    print "KEY: {}".format(key)

    print "Dump decrypted database... "
    conn = sqlite.connect(args.db)
    c = conn.cursor()
    c.execute("PRAGMA key = '" + key + "';")
    c.execute("PRAGMA cipher_use_hmac = OFF;")
    c.execute("PRAGMA cipher_page_size = 1024;")
    c.execute("PRAGMA kdf_iter = 4000;")
    c.execute("ATTACH DATABASE '" + args.output + "' AS db KEY '';")
    c.execute("SELECT sqlcipher_export('db');" )
    c.execute("DETACH DATABASE db;" )
    c.close()
