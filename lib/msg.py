#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: msg.py
# Date: Mon Dec 22 23:04:02 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

from datetime import datetime
from pyquery import PyQuery
from .utils import ensure_bin_str, ensure_unicode

TYPE_MSG = 1
TYPE_IMG = 3
TYPE_SPEAK = 34
TYPE_NAMECARD = 42
TYPE_VIDEO = 43
TYPE_EMOJI = 47
TYPE_LOCATION = 48
TYPE_LINK = 49  # link share OR file from web
TYPE_VOIP = 50
TYPE_SYSTEM = 10000

class WeChatMsg(object):
    FIELDS = ["msgSvrId","type","isSend","createTime","talker","content","imgPath"]

    @staticmethod
    def filter_type(tp):
        if tp in [TYPE_SYSTEM] or tp > 10000 or tp < 0:
            return True
        return False

    def __init__(self, row):
        """ row: a tuple corresponding to FIELDS"""
        assert len(row) == len(WeChatMsg.FIELDS)
        for f, v in zip(WeChatMsg.FIELDS, row):
            setattr(self, f, v)
        self.createTime = datetime.fromtimestamp(self.createTime / 1000)
        self.talker_name = None
        if self.content:
            self.content = ensure_unicode(self.content)
        else:
            self.content = u""

    def msg_str(self):
        if self.type == TYPE_LOCATION:
            pq = PyQuery(self.content)
            loc = pq('location').attr
            label = loc['label']
            try:
                poiname = loc['poiname']
                if poiname:
                    label = poiname
            except:
                pass
            return label + " ({},{})".format(loc['x'], loc['y'])
        elif self.type == TYPE_VOIP:
            return "REQUEST VIDEO CHAT"
        elif self.type == TYPE_LINK:
            pq = PyQuery(self.content)
            url = pq('url').text()
            if not url:
                title = pq('title').text()
                assert title, \
                        u"No title or url found in TYPE_LINK: {}".format(self.content)
                return u"FILE:{}".format(title)
            return u"URL:{}".format(url)
        elif self.type == TYPE_VIDEO:
            return "VIDEO FILE"
        elif self.type == TYPE_NAMECARD:
            pq = PyQuery(self.content)
            msg = pq('msg').attr
            name = msg['nickname']
            if not name:
                name = msg['alias']
            if not name:
                name = ""
            return u"NAMECARD: {}".format(name)
        elif self.type == TYPE_EMOJI:
            # TODO add emoji name
            return self.content
        else:
            return self.content

    def __repr__(self):
        ret = u"{}|{}:{}:{}".format(
            self.type,
            (self.talker if not self.talker_name else self.talker_name) \
                if not self.isSend else 'me',
            self.createTime,
            ensure_unicode(self.msg_str())).encode('utf-8')
        if self.imgPath:
            ret = u"{}|img:{}".format(ensure_unicode(ret.strip()), self.imgPath)
            return ret.encode('utf-8')
        else:
            return ret

    def __lt__(self, r):
        return self.createTime < r.createTime

    def get_emoji_product_id(self):
        assert self.type == TYPE_EMOJI, "Wrong call to get_emoji_product_id()!"
        pq = PyQuery(self.content)
        emoji = pq('emoji')
        if not emoji:
            return None
        return emoji.attrs['productid']
