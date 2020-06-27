#!/bin/bash -e

cat tencent-smiley.json | jq 'to_entries | group_by(.value) | .[] | "---------",.[].key'
