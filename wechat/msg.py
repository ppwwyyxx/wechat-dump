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
        if self.type == TYPE_IMG:
            return "Image"
        elif self.type == TYPE_SPEAK:
            return "Voice"
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
                return "Link"
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
            if self.content.lstrip().startswith("<"):
                return "Emoji"
            if not self.content:
                return "Emoji"
            return self.content
        elif self.type == TYPE_CUSTOM_EMOJI:
            return "Emoji"
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

    def reply_info(self):
        """Parse TYPE_REPLY payload.

        Returns: {title, ref_name, ref_content, ref_type, ref_svrid}.
        """
        if self.type != TYPE_REPLY:
            return None

        def _one_line(text: str, *, max_len: int) -> str:
            text = re.sub(r"\s+", " ", (text or "")).strip()
            if len(text) > max_len:
                return text[: max_len - 1] + "…"
            return text

        xml = self.content_xml_ready
        idx = xml.find("<msg")
        if idx != -1:
            xml = xml[idx:]

        try:
            pq = PyQuery(xml, parser="xml")
        except Exception:
            return None

        title = html.unescape(pq("appmsg > title").text() or pq("title").eq(0).text() or "")

        ref_name_raw = pq("refermsg displayname").text() or pq("refermsg fromusr").text() or ""
        ref_name = _one_line(html.unescape(ref_name_raw), max_len=80)

        ref_content_raw = pq("refermsg content").text() or ""

        ref_svrid_i = None
        ref_svrid = pq("refermsg svrid").text() or pq("refermsg svrId").text()
        if ref_svrid:
            try:
                ref_svrid_i = int(ref_svrid)
            except Exception:
                ref_svrid_i = None

        ref_type_i = None
        ref_type = pq("refermsg type").text()
        if ref_type:
            try:
                ref_type_i = int(ref_type)
            except Exception:
                ref_type_i = None

        ref_content_fallback = html.unescape(ref_content_raw or "")
        if ref_type_i is None:
            ref_content = ref_content_fallback
        else:
            try:
                ref_content = WeChatMsg({"type": ref_type_i, "content": ref_content_fallback}).msg_str()
            except Exception:
                ref_content = ref_content_fallback
        ref_content = _one_line(ref_content, max_len=200)

        if not title and not ref_name and not ref_content:
            return None

        return {
            "title": title.strip(),
            "ref_name": ref_name,
            "ref_content": ref_content,
            "ref_type": ref_type_i,
            "ref_svrid": ref_svrid_i,
        }

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

    def __eq__(self, r):
        return self.createTime == r.createTime and \
                self.talker == r.talker and \
                self.isSend == r.isSend
        # imgPath might change after migration.

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
