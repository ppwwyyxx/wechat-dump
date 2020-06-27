#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import logging
from wechat.parser import WeChatDBParser
from common.textutil import safe_filename
import sys, os

logger = logging.getLogger("wechat")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit("Usage: {0} <path to decoded_database.db> <output_dir>".format(sys.argv[0]))

    db_file = sys.argv[1]
    output_dir = sys.argv[2]
    try:
        os.mkdir(output_dir)
    except:
        pass
    if not os.path.isdir(output_dir):
        sys.exit("Error creating directory {}".format(output_dir))

    parser = WeChatDBParser(db_file)

    for chatid, msgs in parser.msgs_by_chat.items():
        name = parser.contacts[chatid]
        if len(name) == 0:
            logger.info(f"Chat {chatid} doesn't have a valid display name.")
            name = str(id(chatid))
        logger.info(f"Writing msgs for {name}")
        safe_name = safe_filename(name)
        outf = os.path.join(output_dir, safe_name + '.txt')
        if os.path.isfile(outf):
            logger.info(f"File {outf} exists! Skip contact {name}")
            continue
        with open(outf, 'w') as f:
            for m in msgs:
                f.write(str(m))
                f.write("\n")
