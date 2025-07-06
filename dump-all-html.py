#!/usr/bin/env python3
import os
import argparse
import logging
from datetime import datetime

from wechat.parser import WeChatDBParser
from wechat.res import Resource
from wechat.render import HTMLRender

logger = logging.getLogger("wechat")

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', help='output subdirectory', default='output')
    parser.add_argument('--db', default='EnMicroMsg.db.decrypted',
                        help='path to the decrypted database, e.g. EnMicroMsg.db.decrypted')
    parser.add_argument('--res', default='resource', help='the resource directory')
    parser.add_argument('--wxgf-server', help='address of the wxgf image decoder server')
    parser.add_argument('--avt', default='avatar.index', help='path to avatar.index file that only exists in old version of wechat. Ignore for new version of wechat.')
    parser.add_argument('--start', help='start time in format of YYYY-MM-DD HH:MM:SS',
                        type=datetime.fromisoformat)
    parser.add_argument('--skip-existing', action='store_true', help='skip chat if file <output_dir>/<contact>[00].html exists')
    args = parser.parse_args()
    return args

def dump_one(chatid, contact):
    msgs = parser.msgs_by_chat[chatid]
    logger.info(f"Number of Messages for contact {contact}: {len(msgs)}")
    assert len(msgs) > 0
    if args.start is not None:
        msgs = [msg for msg in msgs if msg.createTime > args.start]
        logger.info(f"Number of Messages after {args.start}: {len(msgs)}")

    if args.skip_existing:
        # With current implementation, we don't know if the chat will be split into multiple files
        # until it finishes rendering. Thus we check both the single file and the first split, and
        # skip if either exists.
        # This is not perfect, but it should work unless the user has two contacts, one named XX,
        # and the other named XX00.
        if os.path.exists(args.output_dir + "/" + contact + ".html") or \
           os.path.exists(args.output_dir + "/" + contact + "00.html"):
            logger.warning(f"Output file for {contact} already exists, skipping.")
            return

    render = HTMLRender(parser, res)
    htmls = render.render_msgs(msgs)

    output_file = args.output_dir + "/" + contact + ".html"
    if len(htmls) == 1:
        with open(output_file, 'w') as f:
            f.write(htmls[0])
    else:
        assert output_file.endswith(".html")
        basename = output_file[:-5]
        for idx, html in enumerate(htmls):
            with open(basename + f'{idx:02d}.html', 'w') as f:
                f.write(html)
    res.emoji_reader.flush_cache()

if __name__ == '__main__':
    args = get_args()
    output_dir = args.output_dir
    # Use single instance of WeChatDBParser and Resource to reduce memory footprint
    parser = WeChatDBParser(args.db)
    res = Resource(parser, args.res,
                   wxgf_server=args.wxgf_server,
                   avt_db=args.avt)

    os.makedirs(output_dir, exist_ok=True)

    chats = parser.msgs_by_chat.keys()
    for chatid in chats:
        try:
            contact = parser.contacts[chatid]
        except KeyError:
            contact = chatid
        if len(contact) == 0:
            contact = chatid
        dump_one(chatid, contact)
