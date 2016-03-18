#!/bin/bash -e
# $File: compatibility.sh
# $Date: Tue Jun 16 22:23:36 2015 +0800
# Author: Vury Leo <i[at]vuryleo[dot]com>

if [ `uname` = 'Darwin' ]; then
  GREP='grep -E'
  MD5SUM='md5'
else
  GREP='grep -E'
  MD5SUM='md5sum'
fi

