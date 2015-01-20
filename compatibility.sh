#!/bin/bash -e
# $File: compatibility.sh
# $Date: Mon Jan 19 14:27:25 2015 +0800
# Author: Vury Leo <i[at]vuryleo[dot]com>

realpath() {
  [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

if [ `uname` = 'Darwin' ]
then
  REALPATH='realpath'
  GREP='grep -E'
  MD5SUM='md5'
else
  REALPATH='readlink -f'
  GREP='grep'
  MD5SUM='md5sum'
fi

