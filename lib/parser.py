#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: parser.py
# Date: Wed Dec 17 23:04:54 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import sqlite3
from collections import defaultdict
import itertools
import logging
logger = logging.getLogger(__name__)

from .msg import WeChatMsg
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

        logger.info("Found {} contacts.".format(len(self.contacts)))

    def _parse_msg(self):
        msgs_tot_cnt = 0
        db_msgs = self.cc.execute(
"""
SELECT {} FROM message
""".format(','.join(WeChatMsg.FIELDS)))
        for row in db_msgs:
            msg = WeChatMsg(row)
            if not WeChatMsg.filter_type(msg.type):
                self.msgs_by_talker[msg.talker].append(msg)
        self.msgs_by_talker = dict([
            (self.contacts[k], sorted(v, key=lambda x: x.createTime))
                           for k, v in self.msgs_by_talker.iteritems()])
        for k, v in self.msgs_by_talker.iteritems():
            for msg in v:
                msg.talker_name = ensure_unicode(k)
            msgs_tot_cnt += len(v)
        logger.info("Found {} message records.".format(msgs_tot_cnt))

    def _parse_userinfo(self):
        userinfo_q = self.cc.execute(""" SELECT id, value FROM userinfo """)
        userinfo = dict(userinfo_q)
        self.username = userinfo[2]
        logger.info("Your username is: {}".format(self.username))

    def _parse_imginfo(self):
        imginfo_q = self.cc.execute("""SELECT msgSvrId, bigImgPath FROM ImgInfo2""")
        self.imginfo = dict([(k, v) for (k, v) in imginfo_q
                             if not v.startswith('SERVERID://')])
        logger.info("Found {} big images records.".format(len(self.imginfo)))

    def _find_msg_by_type(self, msgs=None):
        ret = []
        if msgs is None:
            msgs = itertools.chain.from_iterable(self.msgs_by_talker.itervalues())
        for msg in msgs:
            if msg.type == 34:
                ret.append(msg)
        return sorted(ret)

    def parse(self):
        self._parse_userinfo()
        self._parse_contact()
        self._parse_msg()
        self._parse_imginfo()
