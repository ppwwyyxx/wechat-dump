#!/bin/zsh
# File: down1.sh
# Date: Sun Dec 14 01:19:46 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

# Download 105 tencent emoji

for i in {0..104}; do
	size=$(wc -c "$i.png" 2>/dev/null | cut -f 1 -d ' ')
	if [[ -n "$size" && $size -ge 0 ]]; then
		echo "File $i Already There!"
	else
		wget https://wx.qq.com/en_US/htmledition/images/qqface/$i.png &
	fi
done
