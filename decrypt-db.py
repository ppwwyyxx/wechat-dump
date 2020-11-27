#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import struct
import argparse
import logging
import javaobj
from pyquery import PyQuery
from pysqlcipher3 import dbapi2 as sqlite
from hashlib import md5

from wechat.common.procutil import subproc_succ, subproc_call


logger = logging.getLogger("wechat")

RES_DIR = "/mnt/sdcard/tencent/MicroMsg"
MM_DIR = "/data/data/com.tencent.mm"


def get_uin():
    candidates = []
    try:
        uin = None
        out = subproc_succ(f"adb shell cat {MM_DIR}/shared_prefs/system_config_prefs.xml")
        for line in out.decode('utf-8').split("\n"):
            if "default_uin" in line:
                line = PyQuery(line)
                uin = line.attr["value"]
                break
        uin = int(uin)
    except Exception:
        logger.warning("uin not found in system_config_prefs.xml")
    else:
        candidates.append(uin)
        logger.info(f"found uin={uin} in system_config_prefs.xml")

    try:
        uin = None
        out = subproc_succ(f"adb shell cat {MM_DIR}/shared_prefs/com.tencent.mm_preferences.xml")
        for line in out.decode('utf-8').split("\n"):
            if "last_login_uin" in line:
                line = PyQuery(line)
                uin = line.text()
                break
        uin = int(uin)
    except Exception:
        logger.warning("uin not found in com.tencent.mm_preferences.xml")
    else:
        candidates.append(uin)
        logger.info(f"found uin={uin} in com.tencent.mm_preferences.xml")

    try:
        uin = None
        out = subproc_succ(f"adb shell cat {MM_DIR}/shared_prefs/auth_info_key_prefs.xml")
        for line in out.decode('utf-8').split("\n"):
            if "auth_uin" in line:
                line = PyQuery(line)
                uin = line.attr["value"]
                break
        uin = int(uin)
    except Exception:
        logger.warning("uin not found in auth_info_key_prefs.xml")
    else:
        candidates.append(uin)
        logger.info(f"found uin={uin} in auth_info_key_prefs.xml")

    try:
        out = subproc_succ(f"adb shell cat {MM_DIR}/MicroMsg/systemInfo.cfg")
        uin = javaobj.loads(out).get(1, 0)
    except:
        logger.warning("default uin not found in systemInfo.cfg")
    else:
        candidates.append(uin)
        logger.info(f"found uin={uin} in systemInfo.cfg")

    candidates = list({str(x) for x in candidates if x != 0})
    logger.info(f"Possible uin: {candidates}")
    return candidates


def get_imei():
    candidates = []

    class Parcel(object):
        # https://gist.github.com/ktnr74/60ac7bcc2cd17b43f2cb
        def __init__(self, text):
            if text.startswith(b'Result: Parcel(') and text.endswith(b'\')'):
                self.data = b''.join([struct.pack('<L', int(x, 16)) for x in re.findall(b'([0-9a-f]{8}) ', text)])
                self.resultcode = self.get_int(0)
            else:
                raise Exception('Unexpected input!')

        def get_int(self, offset=4):
            return int(struct.unpack('<L', self.data[offset:offset+4])[0])

        def get_utf16(self, offset=4):
            return (self.data[offset + 4: offset+4+self.get_int(offset) * 2]).decode('utf-16')

    out = subproc_succ("adb shell service call iphonesubinfo 1")
    imei = Parcel(out.strip()).get_utf16()
    logger.info(f"found imei={imei} from iphonesubinfo")
    candidates.append(imei)

    try:
        out = subproc_succ(f"adb shell cat {MM_DIR}/MicroMsg/CompatibleInfo.cfg")
        # https://gist.github.com/ChiChou/36556fd412a9e3216abecf06e084e4d9
        jobj = javaobj.loads(out)
        imei = jobj[258]
    except:
        logger.warning("imei not found in CompatibleInfo.cfg")
    else:
        candidates.append(imei)
        logger.info(f"found imei={imei} in CompatibleInfo.cfg")
    candidates.append("1234567890ABCDEF")  # https://github.com/ppwwyyxx/wechat-dump/issues/70
    logger.info(f"Possible imei: {candidates}")
    return list(set(candidates))


def get_key(imei, uin):
    """
    Args:
        imei, uin: str
    """
    if isinstance(uin, str):
        uin = uin.encode('ascii')
    if isinstance(imei, str):
        imei = imei.encode('ascii')
    a = md5(imei + uin)
    return a.hexdigest()[:7]


def do_decrypt(input, output, key):
    conn = sqlite.connect(input)
    c = conn.cursor()
    c.execute("PRAGMA key = '" + key + "';")
    # https://github.com/sqlcipher/sqlcipher/commit/e4b66d6cc8a2b7547a32ff2c3ac52f148eba3516
    c.execute("PRAGMA cipher_compatibility = 1;")
    try:
        c.execute("ATTACH DATABASE '" + output + "' AS db KEY '';")
    except Exception as e:
        logger.error(f"Decryption failed: '{e}'")
        os.unlink(output)
        raise
    logger.info(f"Decryption succeeded! Writing database to {output} ...")
    c.execute("SELECT sqlcipher_export('db');" )
    c.execute("DETACH DATABASE db;" )
    c.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('task', choices=['uin', 'imei', 'decrypt'])
    parser.add_argument('--imei', help='overwrite imei')
    parser.add_argument('--uin', help='overwrite uin')
    parser.add_argument('--input', help='encrypted EnMicroMsg.db')
    args = parser.parse_args()

    subproc_succ("adb root")

    if args.task == 'uin':
        uin = get_uin()
    elif args.task == 'imei':
        imei = get_imei()
    elif args.task == 'decrypt':
        uins = [args.uin] if args.uin else get_uin()
        imeis = [args.imei] if args.imei else get_imei()
        output_file = args.input + ".decrypted"
        assert not os.path.isfile(output_file), f"Output {output_file} exists!"
        for uin in uins:
            for imei in imeis:
                key = get_key(imei, uin)
                logger.info(f"Trying key {key} ...")
                try:
                    do_decrypt(args.input, output_file, key)
                except:
                    pass
                else:
                    logger.info(f"Database dumped to {output_file}")
                    sys.exit()
