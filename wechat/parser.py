#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: parser.py
# Date: Thu Jun 18 00:03:53 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import sqlite3
from collections import defaultdict
import itertools
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from .msg import WeChatMsg
from common.textutil import ensure_unicode

""" tables in concern:
emojiinfo
imginfo2
addr_upload2
chatroom
message
rcontact
"""

class WeChatDBParser(object):
    FIELDS = ["msgSvrId","type","isSend","createTime","talker","content","imgPath"]

    def __init__(self, db_fname):
        """ db_fname: a decoded EnMicroMsg.db"""
        self.db_fname = db_fname
        self.db_conn = sqlite3.connect(self.db_fname)
        self.cc = self.db_conn.cursor()
        self.contacts = {}
        self.msgs_by_chat = defaultdict(list)
        self.emoji_groups = {}
        self.emoji_url = {}
        self.internal_emojis = {}
        self._parse()

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

        self.contacts_rev = {v: k for k, v in self.contacts.iteritems()}
        logger.info("Found {} contacts.".format(len(self.contacts)))

    def _parse_msg(self):
        msgs_tot_cnt = 0
        db_msgs = self.cc.execute(
"""
SELECT {} FROM message
""".format(','.join(WeChatDBParser.FIELDS)))
        for row in db_msgs:
            values = self._parse_msg_row(row)
            if not values:
                continue
            msg = WeChatMsg(values)
            # TODO keep system message?
            if not WeChatMsg.filter_type(msg.type):
                self.msgs_by_chat[msg.chat].append(msg)

        for k, v in self.msgs_by_chat.iteritems():
            self.msgs_by_chat[k] = sorted(v, key=lambda x: x.createTime)
            msgs_tot_cnt += len(v)
        logger.info("Found {} message records.".format(msgs_tot_cnt))

    def _parse_userinfo(self):
        userinfo_q = self.cc.execute(""" SELECT id, value FROM userinfo """)
        userinfo = dict(userinfo_q)
        self.username = userinfo[2]
        logger.info("Your username is: {}".format(self.username))

    def _parse_imginfo(self):
        imginfo_q = self.cc.execute("""SELECT msgSvrId, bigImgPath FROM ImgInfo2""")
        self.imginfo = {k: v for (k, v) in imginfo_q
                             if not v.startswith('SERVERID://')}
        logger.info("Found {} hd image records.".format(len(self.imginfo)))

    def _find_msg_by_type(self, msgs=None):
        ret = []
        if msgs is None:
            msgs = itertools.chain.from_iterable(self.msgs_by_chat.itervalues())
        for msg in msgs:
            if msg.type == 34:
                ret.append(msg)
        return sorted(ret)

    def _parse_emoji(self):
        # wechat provided emojis
        emojiinfo_q = self.cc.execute(
""" SELECT md5, groupid FROM EmojiInfoDesc """)
        for row in emojiinfo_q:
            md5, group = row
            self.emoji_groups[md5] = group

        NEEDED_EMOJI_CATALOG = [49, 50, 17]
        emojiinfo_q = self.cc.execute(
""" SELECT md5, catalog, name, cdnUrl FROM EmojiInfo""")
        for row in emojiinfo_q:
            md5, catalog, name, cdnUrl = row
            if cdnUrl:
                self.emoji_url[md5] = cdnUrl
            if catalog not in NEEDED_EMOJI_CATALOG:
                continue
            self.internal_emojis[md5] = name


    def _parse(self):
        self._parse_userinfo()
        self._parse_contact()
        self._parse_msg()
        self._parse_imginfo()
        self._parse_emoji()

    # process the values in a row
    def _parse_msg_row(self, row):
        """ parse a record of message into my format"""
        values = dict(zip(WeChatDBParser.FIELDS, row))
        if values['content']:
            values['content'] = ensure_unicode(values['content'])
        else:
            values['content'] = u''
        values['createTime'] = datetime.fromtimestamp(values['createTime']/ 1000)
        values['chat'] = values['talker']
        try:
            if values['chat'].endswith('@chatroom'):
                values['chat'] = self.contacts[values['chat']]
                content = values['content']
                talker = content[:content.find(':')]
                try:
                    values['talker'] = self.contacts[talker]
                    values['content'] = content[content.find('\n') + 1:]
                except KeyError:
                    # system messages have no talker
                    values['talker'] = u''
            else:
                tk_id = values['talker']
                values['chat'] = self.contacts[tk_id]
                values['talker'] = self.contacts[tk_id]
        except KeyError:
            # It's possible that messages are kept in database after contacts been deleted
            logger.warn("Unknown contact, probably deleted: {}".format(tk_id))
            return None
        return values
