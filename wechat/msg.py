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

    def reply_info(self):
        """Parse TYPE_REPLY payload.

        Returns: {title, ref_name, ref_content, ref_type, ref_svrid}.
        """
        if self.type != TYPE_REPLY:
            return None

        def _one_line(text: str, *, max_len: int) -> str:
            text = html.unescape(text or "")
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > max_len:
                return text[: max_len - 1] + "…"
            return text

        def _summarize_ref_content(ref_type: int | None, raw: str) -> str:
            raw = html.unescape(raw or "")
            if ref_type == TYPE_IMG:
                return "Image"
            if ref_type == TYPE_SPEAK:
                return "Voice"
            if ref_type in (TYPE_VIDEO_FILE, TYPE_WX_VIDEO):
                return "Video"
            if ref_type == TYPE_LINK:
                xml = raw
                idx = xml.find("<msg")
                if idx != -1:
                    xml = xml[idx:]
                try:
                    root = ET.fromstring(xml)
                    appmsg = root.find("appmsg") or root.find(".//appmsg")
                    if appmsg is None:
                        raise ValueError("missing appmsg")
                    title = _one_line(appmsg.findtext("title") or "", max_len=200)
                    url = _one_line(appmsg.findtext("url") or "", max_len=200)
                    if title:
                        return title
                    if url:
                        return url
                except Exception:
                    pass
                return "Link"
            if ref_type == TYPE_EMOJI or ref_type == TYPE_CUSTOM_EMOJI:
                return "Emoji"

            if ref_type is not None and ref_type != TYPE_MSG:
                # Avoid dumping raw xml blobs for non-text types.
                if raw.lstrip().startswith("<") and len(raw) > 40:
                    return f"[Type {ref_type}]"
            return _one_line(raw, max_len=200)

        xml = self.content_xml_ready
        idx = xml.find("<msg")
        if idx != -1:
            xml = xml[idx:]

        title = ""
        ref_name = ""
        ref_content_raw = ""
        ref_type_i = None
        ref_svrid_i = None

        try:
            root = ET.fromstring(xml)
            appmsg = root.find("appmsg") or root.find(".//appmsg")
            if appmsg is not None:
                title = html.unescape(appmsg.findtext("title") or "")

            refer = root.find(".//refermsg")
            if refer is None and appmsg is not None:
                refer = appmsg.find("refermsg") or appmsg.find(".//refermsg")

            if refer is not None:
                ref_svrid = refer.findtext("svrid") or refer.findtext("svrId")
                try:
                    ref_svrid_i = int(ref_svrid) if ref_svrid else None
                except Exception:
                    ref_svrid_i = None
                ref_type = refer.findtext("type")
                try:
                    ref_type_i = int(ref_type) if ref_type else None
                except Exception:
                    ref_type_i = None
                ref_name = _one_line(refer.findtext("displayname") or refer.findtext("fromusr") or "", max_len=80)
                ref_content_raw = refer.findtext("content") or ""
        except Exception:
            try:
                pq = PyQuery(xml, parser="xml")
                title = html.unescape(pq("title").text() or "")
                ref_name = _one_line(
                    pq("refermsg displayname").text() or pq("refermsg fromusr").text() or "",
                    max_len=80,
                )
                ref_content_raw = pq("refermsg content").text() or ""
                ref_svrid = pq("refermsg svrid").text() or pq("refermsg svrId").text()
                try:
                    ref_svrid_i = int(ref_svrid) if ref_svrid else None
                except Exception:
                    ref_svrid_i = None
                ref_type = pq("refermsg type").text()
                try:
                    ref_type_i = int(ref_type) if ref_type else None
                except Exception:
                    ref_type_i = None
            except Exception:
                return None

        ref_content = _summarize_ref_content(ref_type_i, ref_content_raw)

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
