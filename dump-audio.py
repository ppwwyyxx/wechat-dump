#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# File: dump-audio.py
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import sys
import argparse

from common.textutil import ensure_unicode
from wechat.parser import WeChatDBParser
from wechat.res import Resource
from wechat.render import HTMLRender
from wechat.libchathelper import LibChatHelper

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='name of contact')
    parser.add_argument('--output', help='output mp3 dir', default='/tmp')
    parser.add_argument('--db', default='decrypted.db', help='path to decrypted database')
    parser.add_argument('--res', default='resource', help='reseource directory')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()

    name = ensure_unicode(args.name)
    output_file = args.output

    parser = WeChatDBParser(args.db)
    res = Resource(parser, args.res, '')

    if name and name in parser.msgs_by_chat:
        msgs = parser.msgs_by_chat[name]
    else:
        sys.stderr.write(u"Valid Contacts: {}\n".format(u'\n'.join(parser.msgs_by_chat.keys())))
        sys.stderr.write(u"Couldn't find that contact {}.".format(name));
        sys.exit(1)
    print "Number of Messages: ", len(msgs)
    assert len(msgs) > 0

    libchat = LibChatHelper(parser, res)
    msgs = libchat.convert_msgs(msgs)
    voices = [m.sound for m in msgs if m.sound]
    for idx, v in enumerate(voices):
        p = v.find(':')
        v = v[p:]
        with open('/{}/{:04d}.mp3'.format(args.output, idx), 'wb') as f:
            f.write(v)
