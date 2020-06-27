#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# File: list-chats.py
# Author: Yuxin Wu <ppwwyyxx@gmail.com>

from wechat.parser import WeChatDBParser
import sys
if len(sys.argv) != 2:
    print("Usage: {} db_file".format(sys.argv[0]))
    sys.exit(1)

db_file = sys.argv[1]

parser = WeChatDBParser(db_file)
chats = parser.msgs_by_chat.keys()
for k in chats:
    print(parser.contacts[k], '\t', k)
