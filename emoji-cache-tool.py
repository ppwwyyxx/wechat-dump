#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pickle
import sys
import os
import imghdr
import base64

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("""\
Usage:
 {} unpack output-dir
 {} pack input-dir
""".format(sys.argv[0], sys.argv[0]))
        sys.exit(1)

    if sys.argv[1] == 'unpack':
        with open('emoji.cache', 'rb') as f:
            dic = pickle.load(f)
        outdir = sys.argv[2]
        assert os.path.isdir(outdir)
        for md5, img in dic.items():
            data = img[0]
            if not isinstance(data, bytes):
                data = data.encode('ascii')
            name = os.path.join(outdir, md5 + '.' + img[1].lower())
            print(name)
            with open(name, 'wb') as f:
                f.write(base64.decodebytes(data))
    elif sys.argv[1] == 'pack':
        ret = {}
        indir = sys.argv[2]
        files = os.listdir(indir)
        for fname in files:
            try:
                md5, format = fname.split('.')
            except:
                print("Unable to parse", fname)
                continue
            with open(os.path.join(indir, fname), 'rb') as f:
                b64 = base64.encodebytes(f.read()).decode('ascii')
            ret[md5] = (b64, format)
        with open('emoji.cache', 'wb') as f:
            pickle.dump(ret, f)
