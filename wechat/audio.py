#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import tempfile
import logging
logger = logging.getLogger(__name__)

from .common.textutil import get_file_b64
from .common.procutil import subproc_succ

SILK_DECODER = os.path.join(os.path.dirname(__file__),
                            '../third-party/silk/decoder')

def parse_wechat_audio_file(file_name):
    try:
        return do_parse_wechat_audio_file(file_name)
    except Exception as e:
        logger.error(f"Error when parsing audio file {file_name}: {str(e)}")
        return "", 0

def do_parse_wechat_audio_file(file_name):
    """ return a mp3 stored in base64 unicode string, and the duration"""
    if not file_name: return "", 0

    with tempfile.TemporaryDirectory(prefix="wechatdump_audio") as temp:
        mp3_file = os.path.join(temp,
                                os.path.basename(file_name)[:-4] + '.mp3')
        with open(file_name, 'rb') as f:
            header = f.read(10)
        if b'AMR' in header:
            cmd = f"sox -e signed -c 1 {file_name} {mp3_file}"
            subproc_succ(cmd)
            cmd = f"soxi -D {mp3_file}"
            duration = float(subproc_succ(cmd))

            # The below is python2 only. It should be equivalent to using sox from command line
            # import pysox
            # infile = pysox.CSoxStream(file_name)
            # outfile = pysox.CSoxStream(mp3_file, 'w', infile.get_signal())
            # chain = pysox.CEffectsChain(infile, outfile)
            # chain.flow_effects()
            # outfile.close()
            # signal = infile.get_signal().get_signalinfo()
            # duration = signal['length'] * 1.0 / signal['rate']
        elif b'SILK' in header:
            if not os.path.exists(SILK_DECODER):
                raise RuntimeError("Silk decoder is not compiled. Please see README.md.")

            raw_file = os.path.join(temp,
                                    os.path.basename(file_name)[:-4] + '.raw')
            cmd = '{0} {1} {2}'.format(SILK_DECODER, file_name, raw_file)
            out = subproc_succ(cmd)
            for line in out.split(b'\n'):
                if b'File length' in line:
                    duration = float(line[13:-3].strip())
                    break
            else:
                raise RuntimeError("Error decoding silk audio file!" + out.decode('utf-8'))

            # TODO don't know how to do this with python
            subproc_succ('sox -r 24000 -e signed -b 16 -c 1 {} {}'.format(raw_file, mp3_file))
        else:
            raise NotImplementedError("Audio file format cannot be recognized.")
        mp3_string = get_file_b64(mp3_file)
    return mp3_string, duration

if __name__ == '__main__':
    import sys
    fname = sys.argv[1]
    print(parse_wechat_audio_file(fname)[1])
