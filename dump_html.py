#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: dump_html.py
# Date: Fri Jan 09 22:16:26 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import sys
if len(sys.argv) != 5:
    sys.exit("Usage: {0} <path to decoded_database.db> <path to resource> <name> <output html>".format(sys.argv[0]))

from lib.utils import ensure_unicode
from lib.parser import WeChatDBParser
from lib.res import Resource
from lib.render import HTMLRender

db_file = sys.argv[1]
resource_dir = sys.argv[2]
name = ensure_unicode(sys.argv[3])
output_file = sys.argv[4]

parser = WeChatDBParser(db_file)
msgs = parser.msgs_by_talker[name]
res = Resource(resource_dir)

render = HTMLRender(parser, res)
htmls = render.render_msgs(msgs)

if len(htmls) == 1:
    with open(output_file, 'w') as f:
        print >> f, htmls[0].encode('utf-8')
else:
    for idx, html in enumerate(htmls):
        with open(output_file + '.{}'.format(idx), 'w') as f:
            print >> f, html.encode('utf-8')
