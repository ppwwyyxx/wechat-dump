#!/bin/bash -e
# File: down2.sh
# Date: Sun Dec 14 01:18:45 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

# This script is used to download unicode emoji

emojis=$(cat ../../emojiname.py | grep -o '\\ue[^"]*' | cut -c 3-)
for i in $emojis; do
	size=$(wc -c "$i.png" 2>/dev/null | cut -f 1 -d ' ')
	if [[ -n "$size" && $size -ge 0 ]]; then
		echo "File $i Already There!"
	else
		wget http://www.easyapns.com/emoji/$i.png
	fi
done
