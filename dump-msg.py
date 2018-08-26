#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: dump-msg.py
# Date: Mon May 25 15:23:05 2015 +0800
# Author: Yuxin Wu

from wechat.parser import WeChatDBParser
from common.textutil import safe_filename
import sys, os

if len(sys.argv) != 3:
    sys.exit("Usage: {0} <path to decoded_database.db> <output_dir>".format(sys.argv[0]))

db_file = sys.argv[1]
output_dir = sys.argv[2]
try:
    os.mkdir(output_dir)
except:
    pass
if not os.path.isdir(output_dir):
    sys.exit("Error creating directory {}".format(output_dir))

parser = WeChatDBParser(db_file)

for chatid, msgs in parser.msgs_by_chat.iteritems():
    name = parser.contacts[chatid]
    if len(name) == 0:
        print u"Chat {} doesn't have a valid display name".format(chatid)
        name = str(id(chatid))
    print u"Writing msgs for {}".format(name)
    safe_name = safe_filename(name)
    outf = os.path.join(output_dir, safe_name + '.txt')
    if os.path.isfile(outf):
        print(u"File {} exists! Skip contact {}".format(outf, name))
        continue
    with open(outf, 'w') as f:
        for m in msgs:
            print >> f, m
