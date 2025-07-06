#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import base64
import argparse

from wechat.parser import WeChatDBParser
from wechat.msg import TYPE_SPEAK
from wechat.res import Resource

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='name of contact')
    parser.add_argument('--output', help='output mp3 dir', default='/tmp')
    parser.add_argument('--db', default='decoded.db', help='path to decoded database')
    parser.add_argument('--res', default='resource', help='reseource directory')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()
    parser = WeChatDBParser(args.db)
    res = Resource(parser, args.res)

    try:
        chatid = parser.get_chat_id(args.name)
    except KeyError:
        sys.stderr.write(u"Valid Contacts: {}\n".format('\n'.join(parser.all_chat_nicknames)))
        sys.stderr.write(u"Couldn't find the chat {}.".format(args.name));
        sys.exit(1)

    msgs = parser.msgs_by_chat[chatid]
    print(f"Number of Messages for {args.name}: ", len(msgs))
    assert len(msgs) > 0

    voice_msgs = [m for m in msgs if m.type == TYPE_SPEAK]
    for idx, m in enumerate(voice_msgs):
        audio_str, duration = res.get_voice_mp3(m.imgPath)
        audio_bytes = base64.b64decode(audio_str)
        outf = f'/{args.output}/{idx:04d}-{duration:.1f}s.mp3'
        with open(outf, 'wb') as f:
            f.write(audio_bytes)
        print(f"Audio written to {outf}")
