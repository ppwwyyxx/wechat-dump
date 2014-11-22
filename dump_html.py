#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: dump_html.py
# Date: Sat Nov 22 23:51:45 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import sys
if len(sys.argv) != 3:
    sys.exit("Usage: {0} <path to decoded_database.db> <name>".format(sys.argv[0]))

from lib.utils import ensure_unicode
from lib.parser import WeChatDBParser
from lib.render import HTMLRender

db_file = sys.argv[1]
name = ensure_unicode(sys.argv[2])

parser = WeChatDBParser(db_file)
parser.parse()
msgs = parser.msgs_by_talker[name]

render = HTMLRender()
html = render.render_msgs(msgs).encode('utf-8')
print html
