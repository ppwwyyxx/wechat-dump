#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: audio.py
# Date: Fri Jun 26 10:42:41 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import os
from subprocess import PIPE, Popen, call
import logging
logger = logging.getLogger(__name__)

import pysox

from common.textutil import get_file_b64

SILK_DECODER = os.path.join(os.path.dirname(__file__),
                            '../third-party/silk/decoder')
if not os.path.exists(SILK_DECODER):
    logger.error("Silk decoder is not compiled. Please see README.md.")
    raise RuntimeError()

def parse_wechat_audio_file(file_name):
    try:
        return do_parse_wechat_audio_file(file_name)
    except Exception as e:
        logger.error("Pase audio file {} error!".format(file_name))
        logger.error(e)
        return "", 0

def do_parse_wechat_audio_file(file_name):
    """ return a mp3 base64 string, and the duration"""
    if not file_name: return "", 0

    mp3_file = os.path.join('/tmp',
                            os.path.basename(file_name)[:-4] + '.mp3')
    with open(file_name) as f:
        header = f.read(10)
    if 'AMR' in header:
        # maybe this is faster than calling sox from command line?
        infile = pysox.CSoxStream(file_name)
        outfile = pysox.CSoxStream(mp3_file, 'w', infile.get_signal())
        chain = pysox.CEffectsChain(infile, outfile)
        chain.flow_effects()
        outfile.close()

        signal = infile.get_signal().get_signalinfo()
        duration = signal['length'] * 1.0 / signal['rate']
    elif 'SILK' in header:
        raw_file = os.path.join('/tmp',
                                os.path.basename(file_name)[:-4] + '.raw')
        proc = Popen('{0} {1} {2}'.format(SILK_DECODER,
                                                file_name, raw_file),
                    shell=True, stdout=PIPE, stderr=PIPE)
        stdout = proc.communicate()[0]
        for line in stdout.split('\n'):
            if 'File length' in line:
                duration = float(line[13:-3].strip())
                break
        else:
            raise RuntimeError("Error decoding silk audio file!")

        # I don't know how to do this with pysox
        proc = call('sox -r 24000 -e signed -b 16 -c 1 {} {}'.format(
            raw_file, mp3_file), shell=True)
        os.unlink(raw_file)
    else:
        raise NotImplementedError("Unsupported Audio Format! This is a bug!")
    try:
        mp3_string = get_file_b64(mp3_file)
        os.unlink(mp3_file)
    except:
        raise RuntimeError("Failed to decode audio file: {}".format(file_name))
    return mp3_string, duration

if __name__ == '__main__':
    import sys
    fname = sys.argv[1]
    print parse_wechat_audio_file(fname)[1]
