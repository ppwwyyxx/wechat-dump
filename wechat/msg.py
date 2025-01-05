# -*- coding: UTF-8 -*-
TYPE_MSG = 1
TYPE_IMG = 3
TYPE_SPEAK = 34
TYPE_NAMECARD = 42
TYPE_VIDEO_FILE = 43
TYPE_EMOJI = 47
TYPE_LOCATION = 48
TYPE_LINK = 49  # link share OR file from web, see https://github.com/ppwwyyxx/wechat-dump/issues/52
TYPE_VOIP = 50
TYPE_WX_VIDEO = 62  # video took by wechat
TYPE_SYSTEM = 10000
TYPE_CUSTOM_EMOJI = 1048625
TYPE_REDENVELOPE = 436207665
TYPE_MONEY_TRANSFER = 419430449  # 微信转账
TYPE_LOCATION_SHARING = -1879048186
TYPE_REPLY = 822083633  # 回复的消息.
TYPE_APP_MSG = 16777265

_KNOWN_TYPES = [eval(k) for k in dir() if k.startswith('TYPE_')]

import re
import io
from pyquery import PyQuery
import xml.etree.ElementTree as ET
import logging
logger = logging.getLogger(__name__)

from .common.textutil import ensure_unicode


class WeChatMsg(object):

    @staticmethod
    def filter_type(tp):
        if tp in [TYPE_SYSTEM]:
            return True
        return False

    def __init__(self, values):
        for k, v in values.items():
            setattr(self, k, v)
        if self.type not in _KNOWN_TYPES:
            logger.warn("Unhandled message type: {}".format(self.type))
            # only to supress repeated warning:
            _KNOWN_TYPES.append(self.type)

    def msg_str(self):
        if self.type == TYPE_LOCATION:
            try:
                pq = PyQuery(self.content_xml_ready, parser='xml')
                loc = pq('location').attr
                label = loc['label']
                poiname = loc['poiname']
                if poiname:
                    label = poiname
                return "LOCATION:" + label + " ({},{})".format(loc['x'], loc['y'])
            except:
                return "LOCATION: unknown"
        elif self.type == TYPE_LINK:
            pq = PyQuery(self.content_xml_ready)
            url = pq('url').text()
            if not url:
                # TODO: see https://github.com/ppwwyyxx/wechat-dump/issues/52 for
                # more logic to implement
                title = pq('title').text()
                if title:  # may not be correct
                    return "FILE:{}".format(title)
                return "NOT IMPLEMENTED: " + self.content_xml_ready
            return "URL:{}".format(url)
        elif self.type == TYPE_NAMECARD:
            pq = PyQuery(self.content_xml_ready, parser='xml')
            msg = pq('msg').attr
            name = msg['nickname']
            if not name:
                name = msg['alias']
            if not name:
                name = ""
            return "NAMECARD: {}".format(self.content_xml_ready)
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
            data_to_parse = io.BytesIO(self.content.encode('utf-8'))
            try:
                for event, elem in ET.iterparse(data_to_parse, events=('end',)):
                    if elem.tag == 'sendertitle':
                        title = elem.text
                        return "[RED ENVELOPE]\n{}".format(title)
            except:
                pass
            return "[RED ENVELOPE]"
        elif self.type == TYPE_MONEY_TRANSFER:
            data_to_parse = io.BytesIO(self.content.encode('utf-8'))
            try:
                for event, elem in ET.iterparse(data_to_parse, events=('end',)):
                    if elem.tag == 'des':
                        title = elem.text
                        return "[Money Transfer]\n{}".format(title)
            except:
                pass
            return "[Money Transfer]"
        elif self.type == TYPE_REPLY:
            pq = PyQuery(self.content_xml_ready)
            msg = pq('title').text()
            # TODO parse reply.
            return msg
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
        ret = "{}|{}:{}:{}".format(
            self.type,
            self.talker_nickname if not self.isSend else 'me',
            self.createTime,
            ensure_unicode(self.msg_str()))
        if self.imgPath:
            ret = "{}|img:{}".format(ensure_unicode(ret.strip()), self.imgPath)
            return ret
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

