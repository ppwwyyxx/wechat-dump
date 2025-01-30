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
TYPE_FILE = 1090519089
TYPE_QQMUSIC = 1040187441
TYPE_APP_MSG = 16777265

_KNOWN_TYPES = tuple([eval(k) for k in dir() if k.startswith('TYPE_')])

import re
import json
import io
import html
from pyquery import PyQuery
import xml.etree.ElementTree as ET
import logging
logger = logging.getLogger(__name__)


class WeChatMsg(object):

    @staticmethod
    def filter_type(tp):
        if tp in [TYPE_SYSTEM]:
            return True
        return False

    def __init__(self, values):
        for k, v in values.items():
            setattr(self, k, v)
        self.known_type = self.type in _KNOWN_TYPES

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
            titles = pq('title')
            if len(titles) == 0:
                return self.content_xml_ready
            msg = titles[0].text
            # TODO parse reply.
            return msg
        elif self.type == TYPE_FILE:
            pq = PyQuery(self.content_xml_ready)
            titles = pq('title')
            if len(titles) == 0:
                return self.content_xml_ready
            return "FILE:" + titles[0].text
        elif self.type == TYPE_QQMUSIC:
            pq = PyQuery(self.content_xml_ready)
            title = pq('title')[0].text
            singer = pq('des')[0].text
            url = html.unescape(pq('url')[0].text)
            return json.dumps(dict(
                title=title, singer=singer, url=url
            ))
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
            self.msg_str())
        if self.imgPath:
            ret = "{}|img:{}".format(ret.strip(), self.imgPath)
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

