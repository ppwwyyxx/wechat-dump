#!/bin/bash -e
# File: see_smiley_name.sh
# Date: Sun Jan 11 21:37:06 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

cat tencent-smiley.json | jq 'to_entries | group_by(.value) | .[] | "---------",.[].key'
