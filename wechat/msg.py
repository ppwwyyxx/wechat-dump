#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: msg.py
# Date: Thu Jun 18 00:01:00 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>
TYPE_MSG = 1
TYPE_IMG = 3
TYPE_SPEAK = 34
TYPE_NAMECARD = 42
TYPE_VIDEO_FILE = 43
TYPE_EMOJI = 47
TYPE_LOCATION = 48
TYPE_LINK = 49  # link share OR file from web
TYPE_VOIP = 50
TYPE_WX_VIDEO = 62  # video took by wechat
TYPE_SYSTEM = 10000
TYPE_CUSTOM_EMOJI = 1048625
TYPE_REDENVELOPE = 436207665
TYPE_LOCATION_SHARING = -1879048186
TYPE_APP_MSG = 16777265
#TYPE_? = 35 QQMail assist
#TYPE_? = 10002 Chatroom member
#TYPE_? = 64 Voice talk
#TYPE_? = 318767153 Didi
#TYPE_? = 419430449 Transfer

_KNOWN_TYPES = [eval(k) for k in dir() if k.startswith('TYPE_')]

import re
from pyquery import PyQuery
import logging
logger = logging.getLogger(__name__)

from common.textutil import ensure_unicode


class WeChatMsg(object):

    @staticmethod
    def filter_type(tp):
        if tp in [TYPE_SYSTEM]:
            return True
        return False

    def __init__(self, values):
        for k, v in values.iteritems():
            setattr(self, k, v)
        if self.type not in _KNOWN_TYPES:
            logger.warn("Unhandled message type: {}".format(self.type))
            # only to supress repeated warning:
            _KNOWN_TYPES.append(self.type)

    def msg_str(self):
        if self.type == TYPE_LOCATION:
            pq = PyQuery(self.content_xml_ready.replace('poiname', ' poiname'), parser='xml')
            loc = pq('location').attr
            label = loc['label']
            try:
                poiname = loc['poiname']
                if poiname:
                    label = poiname
            except:
                pass
            return "LOCATION:" + label + " ({},{})".format(loc['x'], loc['y'])
        elif self.type == TYPE_LINK:
            pq = PyQuery(self.content_xml_ready)
            url = pq('url').text()
            if not url:
                title = pq('title').text()
                assert title, \
                        u"No title or url found in TYPE_LINK: {}".format(self.content)
                return u"FILE:{}".format(title)
            return u"URL:{}".format(url)
        elif self.type == TYPE_NAMECARD:
            pq = PyQuery(self.content_xml_ready, parser='xml')
            msg = pq('msg').attr
            name = msg['nickname']
            if not name:
                name = msg['alias']
            if not name:
                name = ""
            return u"NAMECARD: {}".format(self.content_xml_ready)
        elif self.type == TYPE_APP_MSG:
            pq = PyQuery(self.content_xml_ready, parser='xml')
            return pq('title').text()
        elif self.type == TYPE_VIDEO_FILE:
            return "VIDEO FILE"
        elif self.type == TYPE_WX_VIDEO:
            return "WeChat VIDEO"
        elif self.type == TYPE_VOIP:
            return "REQUEST VIDEO CHAT"
        elif self.type == TYPE_LOCATION_SHARING:
            return "LOCATION SHARING"
        elif self.type == TYPE_EMOJI:
            # TODO add emoji name
            return self.content
        elif self.type == TYPE_REDENVELOPE:
            pq = PyQuery(self.content_xml_ready, parser='xml')

            title = pq('sendertitle').text()
            return u"[RED ENVELOPE]\n{}".format(title)
        else:
            # TODO replace smiley with text
            return self.content

    @property
    def content_xml_ready(self):
        # remove xml headers to avoid possible errors it may create
        header = re.compile(r'<\?.*\?>')
        msg = header.sub("", self.content)
        return msg

    def __repr__(self):
        ret = u"{}|{}:{}:{}".format(
            self.type,
            self.talker_nickname if not self.isSend else 'me',
            self.createTime,
            ensure_unicode(self.msg_str())).encode('utf-8')
        if self.imgPath:
            ret = u"{}|img:{}".format(ensure_unicode(ret.strip()), self.imgPath)
            return ret.encode('utf-8')
        else:
            return ret

    def __lt__(self, r):
        return self.createTime < r.createTime

    def is_chatroom(self):
        return self.talker != self.chat

    def get_chatroom(self):
        if self.is_chatroom():
            return self.chat
        else:
            return ''

    def get_emoji_product_id(self):
        assert self.type == TYPE_EMOJI, "Wrong call to get_emoji_product_id()!"
        pq = PyQuery(self.content_xml_ready, parser='xml')
        emoji = pq('emoji')
        if not emoji:
            return None
        return emoji.attrs['productid']

