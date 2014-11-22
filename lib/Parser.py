#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: Parser.py
# Date: Sat Nov 22 08:07:56 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import sqlite3
from collections import defaultdict
import itertools

from .Msg import WeChatMsg
from .utils import ensure_unicode

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
        self.msgs_by_talker = defaultdict(list)

    def _parse_contact(self):
        contacts = self.cc.execute(
"""
SELECT username,conRemark,nickname FROM rcontact
""")
        for row in contacts:
            username, remark, nickname = row
            if remark:
                self.contacts[username] = ensure_unicode(remark)
            else:
                self.contacts[username] = ensure_unicode(nickname)

    def _parse_msg(self):
        db_msgs = self.cc.execute(
"""
SELECT {} FROM message
""".format(','.join(WeChatMsg.FIELDS)))
        for row in db_msgs:
            msg = WeChatMsg(row)
            if msg.type not in WeChatMsg.FILTER_TYPES:
                self.msgs_by_talker[msg.talker].append(msg)
        self.msgs_by_talker = dict([
            (self.contacts[k], sorted(v, key=lambda x: x.createTime))
                           for k, v in self.msgs_by_talker.iteritems()])
        for k, v in self.msgs_by_talker.iteritems():
            for msg in v:
                msg.talker = k

    def _find_msg_by_type(self, msgs=None):
        ret = []
        if msgs is None:
            msgs = itertools.chain.from_iterable(self.msgs_by_talker.itervalues())
        for msg in msgs:
            if msg.type == 43:
                ret.append(msg)
        return sorted(ret)

    def parse(self):
        self._parse_contact()
        self._parse_msg()
