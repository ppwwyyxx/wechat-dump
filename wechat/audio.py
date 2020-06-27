#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import logging
logger = logging.getLogger(__name__)

from common.textutil import get_file_b64
from common.procutil import subproc_succ

SILK_DECODER = os.path.join(os.path.dirname(__file__),
                            '../third-party/silk/decoder')
if not os.path.exists(SILK_DECODER):
    logger.error("Silk decoder is not compiled. Please see README.md.")
    raise RuntimeError()

def parse_wechat_audio_file(file_name):
    try:
        return do_parse_wechat_audio_file(file_name)
    except Exception as e:
        logger.exception("Error when parsing audio file {}".format(file_name))
        return "", 0

def do_parse_wechat_audio_file(file_name):
    """ return a mp3 stored in base64 unicode string, and the duration"""
    if not file_name: return "", 0

    mp3_file = os.path.join('/tmp',
                            os.path.basename(file_name)[:-4] + '.mp3')
    with open(file_name, 'rb') as f:
        header = f.read(10)
    if b'AMR' in header:
        raise NotImplementedError("AMR decoding not implemented because it seems deprecated since WeChat6.0+")
        # The below is python2 only. It should be equivalent to using sox from command line?
        import pysox
        infile = pysox.CSoxStream(file_name)
        outfile = pysox.CSoxStream(mp3_file, 'w', infile.get_signal())
        chain = pysox.CEffectsChain(infile, outfile)
        chain.flow_effects()
        outfile.close()
        signal = infile.get_signal().get_signalinfo()
        duration = signal['length'] * 1.0 / signal['rate']
    elif b'SILK' in header:
        raw_file = os.path.join('/tmp',
                                os.path.basename(file_name)[:-4] + '.raw')
        cmd = '{0} {1} {2}'.format(SILK_DECODER, file_name, raw_file)
        out = subproc_succ(cmd)
        for line in out.split(b'\n'):
            if b'File length' in line:
                duration = float(line[13:-3].strip())
                break
        else:
            raise RuntimeError("Error decoding silk audio file!")

        # TODO don't know how to do this with python
        subproc_succ('sox -r 24000 -e signed -b 16 -c 1 {} {}'.format(raw_file, mp3_file))
        os.unlink(raw_file)
    else:
        raise NotImplementedError("Unsupported Audio Format! This is a bug!")
    mp3_string = get_file_b64(mp3_file)
    os.unlink(mp3_file)
    return mp3_string, duration

if __name__ == '__main__':
    import sys
    fname = sys.argv[1]
    print(parse_wechat_audio_file(fname)[1])
