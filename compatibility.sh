#!/bin/bash -e
# $File: compatibility.sh
# $Date: Sun Feb 01 17:22:34 2015 +0800
# Author: Vury Leo <i[at]vuryleo[dot]com>

realpath() {
  [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

if [ `uname` = 'Darwin' ]; then
  REALPATH='realpath'
  GREP='grep -E'
  MD5SUM='md5'
else
  REALPATH='readlink -f'
  GREP=grep
  MD5SUM='md5sum'
fi

