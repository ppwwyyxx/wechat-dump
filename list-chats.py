#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: list-chats.py
# Author: Yuxin Wu <ppwwyyxx@gmail.com>

from wechat.parser import WeChatDBParser
import sys

db_file = sys.argv[1]

parser = WeChatDBParser(db_file)
chats = parser.msgs_by_chat.keys()
for k in chats:
    print k.encode('utf-8'), parser.contacts_rev[k].encode('utf-8')
