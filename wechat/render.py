#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
from collections import Counter
from functools import lru_cache
import glob
from pyquery import PyQuery
import logging
logger = logging.getLogger(__name__)

LIB_PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_PATH = os.path.join(LIB_PATH, 'static')
HTML_FILE = os.path.join(STATIC_PATH, 'TP_INDEX.html')
TIME_HTML_FILE = os.path.join(STATIC_PATH, 'TP_TIME.html')
FRIEND_AVATAR_CSS_FILE = os.path.join(STATIC_PATH, 'avatar.css.tpl')

try:
    from csscompressor import compress as css_compress
except ImportError:
    css_compress = lambda x: x

from .msg import *
from .common.textutil import get_file_b64
from .common.progress import ProgressReporter
from .common.timer import timing
from .smiley import SmileyProvider
from .msgslice import MessageSlicerByTime, MessageSlicerBySize

TEMPLATES_FILES = {TYPE_MSG: "TP_MSG",
                   TYPE_IMG: "TP_IMG",
                   TYPE_SPEAK: "TP_SPEAK",
                   TYPE_EMOJI: "TP_EMOJI",
                   TYPE_CUSTOM_EMOJI: "TP_EMOJI",
                   TYPE_LINK: "TP_MSG",
                   TYPE_REPLY: "TP_REPLY",
                   TYPE_VIDEO_FILE: "TP_VIDEO_FILE",
                   TYPE_QQMUSIC: "TP_QQMUSIC",
                  }


@lru_cache()
def get_template(name: str | int) -> str | None:
    """Return the html template given a file name or msg type."""
    if isinstance(name, int):
        name = TEMPLATES_FILES.get(name, None)
        if name is None:
            return None
    html_path = os.path.join(STATIC_PATH, f"{name}.html")
    with open(html_path) as f:
        return f.read()


class HTMLRender(object):
    def __init__(self, parser, res=None):
        with open(HTML_FILE) as f:
            self.html = f.read()
        with open(TIME_HTML_FILE) as f:
            self.time_html = f.read()
        self.parser = parser
        self.res = res
        assert self.res is not None, \
            "Resource Directory not given. Cannot render HTML."
        self.smiley = SmileyProvider()

        css_files = glob.glob(os.path.join(LIB_PATH, 'static/*.css'))
        self.css_string = []    # css to add
        for css in css_files:
            logger.info("Loading {}".format(os.path.basename(css)))
            with open(css) as f:
                self.css_string.append(f.read())

        js_files = glob.glob(os.path.join(LIB_PATH, 'static/*.js'))
        # to load jquery before other js
        js_files = sorted(js_files, key=lambda f: 'jquery-latest' in f, reverse=True)
        self.js_string = []
        for js in js_files:
            logger.info("Loading {}".format(os.path.basename(js)))
            with open(js) as f:
                self.js_string.append(f.read())

        self.unknown_type_cnt = Counter()

    @property
    def all_css(self):
        # call after processing all messages,
        # because smiley css need to be included only when necessary
        def process(css):
            css = css_compress(css)
            return u'<style type="text/css">{}</style>'.format(css)

        if hasattr(self, 'final_css'):
            return self.final_css + process(self.smiley.gen_used_smiley_css())

        self.final_css = u"\n".join(map(process, self.css_string))
        return self.final_css + process(self.smiley.gen_used_smiley_css())

    @property
    def all_js(self):
        if hasattr(self, 'final_js'):
            return self.final_js
        def process(js):
            # TODO: add js compress
            return u'<script type="text/javascript">{}</script>'.format(js)
        self.final_js = u"\n".join(map(process, self.js_string))
        return self.final_js

    #@timing(total=True)
    def render_msg(self, msg: WeChatMsg):
        """ render a message, return the html block"""
        # TODO for chatroom, add nickname on avatar
        sender = u'you ' + msg.talker if not msg.isSend else 'me'
        format_dict = {'sender_label': sender,
                       'time': msg.createTime }
        if not msg.known_type:
            self.unknown_type_cnt[msg.type] += 1
        if(not msg.isSend and msg.is_chatroom()):
            format_dict['nickname'] = '>\n       <pre align=\'left\'>'+msg.talker_nickname+'</pre'
        else:
            format_dict['nickname'] = ' '

        def fallback():
            template = get_template(TYPE_MSG)
            content = msg.msg_str()
            content = self.smiley.replace_smileycode(content)
            if not msg.known_type:
                # Show raw (usually xml) content if unknown.
                content = html.escape(content)
            return template.format(content=content, **format_dict)

        template = get_template(msg.type)
        if msg.type == TYPE_SPEAK:
            audio_str, duration = self.res.get_voice_mp3(msg.imgPath)
            format_dict['voice_duration'] = duration
            format_dict['voice_str'] = audio_str
            return template.format(**format_dict)
        elif msg.type == TYPE_IMG:
            # imgPath was original THUMBNAIL_DIRPATH://th_xxxxxxxxx
            imgpath = msg.imgPath.split('_')[-1]
            if not imgpath:
                logger.warn('No imgpath in an image message. Perhaps a bug in wechat.')
                return fallback()
            bigimgpath = self.parser.imginfo.get(msg.msgSvrId)
            fnames = [k for k in [imgpath, bigimgpath] if k]
            img = self.res.get_img(fnames)
            if not img:
                logger.warn("No image thumbnail found for {}".format(imgpath))
                return fallback()
            # TODO do not show fancybox when no bigimg found
            format_dict['img'] = (img, 'jpeg')
            return template.format(**format_dict)
        elif msg.type == TYPE_QQMUSIC:
            jobj = json.loads(msg.msg_str())
            content = f"{jobj['title']} - {jobj['singer']}"

            if msg.imgPath is not None:
                # imgPath was original THUMBNAIL_DIRPATH://th_xxxxxxxxx
                imgpath = msg.imgPath.split('_')[-1]
                img = self.res.get_img([imgpath])
                format_dict['img'] = (img, 'jpeg')
            else:
                template = get_template("TP_QQMUSIC_NOIMG")
            return template.format(url=jobj['url'], content=content, **format_dict)
        elif msg.type == TYPE_REPLY:
            info = msg.reply_info()
            if not info:
                return fallback()

            def _escape_fmt(s: str) -> str:
                return s.replace("{", "{{").replace("}", "}}")

            title = info.get("title") or ""
            reply_to = info.get("ref_name") or "unknown"
            reply_quote = info.get("ref_content") or ""
            ref_svrid = info.get("ref_svrid")

            if not title and not reply_quote:
                return fallback()

            format_dict["content"] = _escape_fmt(self.smiley.replace_smileycode(title))
            format_dict["reply_to"] = _escape_fmt(reply_to)

            reply_thumb_html = ""
            ref_msg = getattr(self, "_msg_by_svrid", {}).get(ref_svrid) if ref_svrid is not None else None
            if ref_msg is not None:
                try:
                    if ref_msg.type == TYPE_IMG and ref_msg.imgPath:
                        imgpath = ref_msg.imgPath.split("_")[-1]
                        bigimgpath = self.parser.imginfo.get(ref_msg.msgSvrId)
                        fnames = [k for k in [imgpath, bigimgpath] if k]
                        b64 = self.res.get_img_thumb(fnames, max_size=64)
                        if b64:
                            reply_thumb_html = f'<img class="replyThumb" src="data:image/jpeg;base64,{b64}" />'
                    elif ref_msg.type in (TYPE_VIDEO_FILE, TYPE_WX_VIDEO) and ref_msg.imgPath:
                        b64 = self.res.get_video_thumb(ref_msg.imgPath, max_size=64)
                        if b64:
                            reply_thumb_html = f'<img class="replyThumb" src="data:image/jpeg;base64,{b64}" />'
                    elif ref_msg.type in (TYPE_EMOJI, TYPE_CUSTOM_EMOJI):
                        if "emoticonmd5" in ref_msg.content:
                            pq = PyQuery(ref_msg.content)
                            md5 = pq("emoticonmd5").text()
                        else:
                            md5 = ref_msg.imgPath
                        if md5:
                            emoji_img, fmt = self.res.get_emoji_by_md5(md5)
                            if emoji_img and fmt:
                                fmt = fmt.lower()
                                if fmt == "jpg":
                                    fmt = "jpeg"
                                reply_thumb_html = (
                                    f'<img class="replyThumb replyThumbEmoji" '
                                    f'src="data:image/{fmt};base64,{emoji_img}" />'
                                )
                except Exception:
                    logger.exception("Failed to render reply thumbnail (%s).", ref_svrid)

            if reply_thumb_html:
                reply_quote_html = reply_thumb_html
            else:
                quote_text = self.smiley.replace_smileycode(reply_quote)
                reply_quote_html = f'<span class="replyText">{quote_text}</span>'
            format_dict["reply_quote_html"] = _escape_fmt(reply_quote_html)

            template = template or get_template(TYPE_MSG)
            return template.format(**format_dict)
        elif msg.type == TYPE_EMOJI or msg.type == TYPE_CUSTOM_EMOJI:
            if 'emoticonmd5' in msg.content:
                pq = PyQuery(msg.content)
                md5 = pq('emoticonmd5').text()
            else:
                md5 = msg.imgPath
                # TODO md5 could exist in both.
                # first is emoji md5, second is image2/ md5
                # can use fallback here.
            if md5:
                emoji_img, format = self.res.get_emoji_by_md5(md5)
                format_dict['emoji_format'] = format
                format_dict['emoji_img'] = emoji_img
            else:
                import IPython as IP; IP.embed()
            return template.format(**format_dict)
        elif msg.type == TYPE_LINK:
            pq = PyQuery(msg.content_xml_ready)
            url = pq('url').text()
            if url:
                try:
                    title = pq('title')[0].text
                except Exception as e:
                    logger.warning('No title found in LINK message: ' + str(e))
                    title = url
                content = '<a target="_blank" href="{0}">{1}</a>'.format(url, title)
                format_dict['content'] = content
                return template.format(**format_dict)
        elif msg.type == TYPE_VIDEO_FILE:
            video = self.res.get_video(msg.imgPath)
            if video is None:
                logger.warning(f"Cannot find video {msg.imgPath} ({msg.createTime})")
                # fallback
                format_dict['content'] = f"VIDEO FILE {msg.imgPath}"
                return get_template(TYPE_MSG).format(**format_dict)
            elif video.endswith(".mp4"):
                video_str = get_file_b64(video)
                format_dict["video_str"] = video_str
                return template.format(**format_dict)
            elif video.endswith(".jpg"):
                # only has thumbnail
                image_str = get_file_b64(video)
                format_dict["img"] = (image_str, 'jpeg')
                return get_template(TYPE_IMG).format(**format_dict)
        elif msg.type == TYPE_WX_VIDEO:
            # TODO: fetch video from resource
            return fallback()
        return fallback()

    def _render_partial_msgs(self, msgs):
        """ return single html"""
        self.smiley.reset()
        slicer = MessageSlicerByTime()
        slices = slicer.slice(msgs)

        blocks = []
        for idx, slice in enumerate(slices):
            nowtime = slice[0].createTime
            if idx == 0 or \
               slices[idx - 1][0].createTime.date() != nowtime.date():
                timestr = nowtime.strftime("%m/%d %H:%M:%S")
            else:
                timestr = nowtime.strftime("%H:%M:%S")
            blocks.append(self.time_html.format(time=timestr))
            blocks.extend([self.render_msg(m) for m in slice])
            self.prgs.trigger(len(slice))

        # string operation is extremely slow
        return self.html.format(extra_css=self.all_css,
                            extra_js=self.all_js,
                            chat=msgs[0].chat_nickname,
                            messages=u''.join(blocks)
                           )

    def prepare_avatar_css(self, talkers):
        with open(FRIEND_AVATAR_CSS_FILE) as f:
            avatar_tpl = f.read()
        my_avatar = self.res.get_avatar(self.parser.username)
        css = avatar_tpl.format(name='me', avatar=my_avatar)

        for talker in talkers:
            avatar = self.res.get_avatar(talker)
            css += avatar_tpl.format(name=talker, avatar=avatar)
        self.css_string.append(css)

    def render_msgs(self, msgs):
        """ render msgs of one chat, return a list of html"""
        chatid = msgs[0].chat
        self._msg_by_svrid = {m.msgSvrId: m for m in self.parser.msgs_by_chat.get(chatid, msgs)}
        if msgs[0].is_chatroom():
            talkers = set([m.talker for m in msgs])
        else:
            talkers = set([msgs[0].talker])
        self.prepare_avatar_css(talkers)

        self.res.cache_voice_mp3(msgs)

        chat = msgs[0].chat_nickname
        logger.info(u"Rendering {} messages of {}".format(
            len(msgs), chat))

        self.prgs = ProgressReporter("Render", total=len(msgs))
        slice_by_size = MessageSlicerBySize().slice(msgs)
        ret = [self._render_partial_msgs(s) for s in slice_by_size]
        self.prgs.finish()
        logger.warning("[HTMLRenderer] Unhandled messages (type->cnt): {}".format(self.unknown_type_cnt))
        return ret

if __name__ == '__main__':
    r = HTMLRender()
    with open('/tmp/a.html', 'w') as f:
        print >> f, r.html.format(style=r.css, talker='talker',
                                     messages='haha')
