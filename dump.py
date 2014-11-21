#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: dump.py
# Date: Fri Nov 21 13:07:58 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import sqlite3
from collections import defaultdict
from pprint import PrettyPrinter
pp = PrettyPrinter()
def log(x): print repr(x).decode('unicode-escape')
from lib.Msg import WeChatMsg

""" tables in concern:
emojiinfo
imginfo2
addr_upload2
chatroom
message
rcontact

"""

class WeChatDBParser(object):
    def __init__(self, db_fname):
        """ db_fname: EnMicroMsg.db"""
        self.db_fname = db_fname
        self.db_conn = sqlite3.connect(self.db_fname)
        self.cc = self.db_conn.cursor()
        self.contacts = {}

    def _parse_contact(self):
        contacts = self.cc.execute(
"""
SELECT username,conRemark,nickname
FROM rcontact
""")
        for row in contacts:
            username, remark, nickname = row
            if remark:
                self.contacts[username] = remark
            else:
                self.contacts[username] = nickname

    def _parse_msg(self):
        msgs_by_talker = defaultdict(list)
        db_msgs = self.cc.execute(
"""
SELECT {}
FROM message ORDER BY createTime
""".format(','.join(WeChatMsg.FIELDS)))
        for row in db_msgs:
            msg = WeChatMsg(row)
            msgs_by_talker[msg.talker].append(msg)
        msgs_by_talker = dict([
            (self.contacts[k], sorted(v, key=lambda x: x.createTime))
                           for k, v in msgs_by_talker.iteritems()])
        for k, v in msgs_by_talker.iteritems():
            for msg in v:
                msg.talker = k
        pp.pprint(msgs_by_talker.items()[0])

    def parse(self):
        self._parse_contact()
        msg = self._parse_msg()
        pass

if __name__ == '__main__':
    parser = WeChatDBParser('./decoded_database.db')
    parser.parse()
