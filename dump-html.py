#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: dump-html.py
# Date: Wed Mar 25 17:44:20 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import sys
if len(sys.argv) != 6:
    sys.exit("Usage: {0} <path to decrypted_database.db> <path to avatar.index> <path to resource> <name> <output html>".format(sys.argv[0]))

from common.textutil import ensure_unicode
from wechat.parser import WeChatDBParser
from wechat.res import Resource
from wechat.render import HTMLRender

db_file = sys.argv[1]
avt_db = sys.argv[2]
resource_dir = sys.argv[3]
name = ensure_unicode(sys.argv[4])
output_file = sys.argv[5]

parser = WeChatDBParser(db_file)
res = Resource(resource_dir, avt_db)

try:
    msgs = parser.msgs_by_chat[name]
except:
    sys.stderr.write(u"Valid Contacts: {}\n".format(u'\n'.join(parser.msgs_by_chat.keys())))
    sys.stderr.write(u"Couldn't find that contact {}.".format(name));
    sys.exit(1)

render = HTMLRender(parser, res)
htmls = render.render_msgs(msgs)

if len(htmls) == 1:
    with open(output_file, 'w') as f:
        print >> f, htmls[0].encode('utf-8')
else:
    for idx, html in enumerate(htmls):
        with open(output_file + '.{}'.format(idx), 'w') as f:
            print >> f, html.encode('utf-8')
