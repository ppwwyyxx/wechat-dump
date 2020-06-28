#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import argparse
import logging

from common.textutil import ensure_unicode
from wechat.parser import WeChatDBParser
from wechat.res import Resource
from wechat.render import HTMLRender

logger = logging.getLogger("wechat")

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='name of contact')
    parser.add_argument('--output', help='output html file', default='output.html')
    parser.add_argument('--db', default='decoded.db', help='path to decoded database')
    parser.add_argument('--avt', default='avatar.index', help='path to avatar.index file')
    parser.add_argument('--res', default='resource', help='reseource directory')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()

    name = ensure_unicode(args.name)
    output_file = args.output

    parser = WeChatDBParser(args.db)

    try:
        chatid = parser.get_id_by_nickname(name)
    except KeyError:
        sys.stderr.write(u"Valid Contacts: {}\n".format(
            u'\n'.join(parser.all_chat_nicknames)))
        sys.stderr.write(u"Couldn't find the chat {}.".format(name));
        sys.exit(1)
    res = Resource(parser, args.res, args.avt)
    msgs = parser.msgs_by_chat[chatid]
    logger.info(f"Number of Messages: {len(msgs)}")
    assert len(msgs) > 0

    render = HTMLRender(parser, res)
    htmls = render.render_msgs(msgs)

    if len(htmls) == 1:
        with open(output_file, 'w') as f:
            f.write(htmls[0])
    else:
        assert output_file.endswith(".html")
        basename = output_file[:-5]
        for idx, html in enumerate(htmls):
            with open(basename + f'{idx:02d}.html', 'w') as f:
                f.write(html)
    res.emoji_cache.flush()
