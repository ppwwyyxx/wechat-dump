#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: dump_msg.py
# Date: Wed Mar 25 17:44:34 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

from wechat.parser import WeChatDBParser
import sys, os

if len(sys.argv) != 3:
    sys.exit("Usage: {0} <path to decrypted_database.db> <output_dir>".format(sys.argv[0]))

db_file = sys.argv[1]
output_dir = sys.argv[2]
try:
    os.mkdir(output_dir)
except:
    pass
if not os.path.isdir(output_dir):
    sys.exit("Error creating directory {}".format(output_dir))

parser = WeChatDBParser(db_file)

for name, msgs in parser.msgs_by_talker.iteritems():
    print u"Writing msgs for {}".format(name)
    with open(os.path.join(output_dir, name + '.txt'), 'w') as f:
        for m in msgs:
            print >> f, m
