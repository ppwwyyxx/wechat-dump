#!/bin/bash
# File: android-interact.sh
# Date: Fri Jun 26 10:38:07 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

PROG_NAME=`python -c "import os, sys; print(os.path.realpath(sys.argv[1]))" "$0"`
PROG_DIR=`dirname "$PROG_NAME"`
cd "$PROG_DIR"

source compatibility.sh

# Please check that your path is the same, since this might be different among devices
RES_DIR="/mnt/sdcard/tencent/MicroMsg"
MM_DIR="/data/data/com.tencent.mm"

echo "Starting rooted adb server..."
adb root

if [[ $1 == "uin" ]]; then
	adb pull $MM_DIR/shared_prefs/system_config_prefs.xml 2>/dev/null
	uin=$($GREP 'default_uin' system_config_prefs.xml | $GREP -o 'value=\"\-?[0-9]*' | cut -c 8-)
	[[ -n $uin ]] || {
		>&2 echo "Failed to get wechat uin. You can try other methods, or report a bug."
		exit 1
	}
	rm system_config_prefs.xml
	echo "Got wechat uin: $uin"
elif [[ $1 == "imei" ]]; then
	imei=$(adb shell dumpsys iphonesubinfo | $GREP 'Device ID' | $GREP -o '[0-9]+')
	[[ -n $imei ]] || {
		imei=$(adb shell service call iphonesubinfo 1 | awk -F "'" '{print $2}' | sed 's/[^0-9A-F]*//g' | tr -d '\n')
	}
	[[ -n $imei ]] || {
		>&2 echo "Failed to get imei. You can try other methods, or report a bug."
		exit 1
	}
	echo "Got imei: $imei"
elif [[ $1 == "db" || $1 == "res" ]]; then
	echo "Looking for user dir name..."
	sleep 1  	# sometimes adb complains: device not found
	# look for dirname which looks like md5 (32 alpha-numeric chars)
	userList=$(adb ls $RES_DIR | cut -f 4 -d ' ' | sed 's/[^0-9a-z]//g' \
		| awk '{if (length() == 32) print}')
	numUser=$(echo "$userList" | wc -l)
	# choose the first user.
	chooseUser=$(echo "$userList" | head -n1)
	[[ -n $chooseUser ]] || {
		>&2 echo "Could not find user. Please check whether your resource dir is $RES_DIR"
		exit 1
	}
	echo "Found $numUser user(s). User chosen: $chooseUser"

	if [[ $1 == "res" ]]; then
		echo "Pulling resources... this might take a long time, because adb sucks..."
		mkdir -p resource; cd resource
		for d in image2 voice2 emoji video sfs; do
			mkdir -p $d; cd $d
			adb pull "$RES_DIR/$chooseUser/$d"
			cd ..
			[[ -d $d ]] || {
				>&2 echo "Failed to download resource directory: $RES_DIR/$chooseUser/$d"
				exit 1
			}
		done
		cd ..
		echo "Resource pulled at ./resource"
		echo "Total size: $(du -sh resource | cut -f1)"
	else
		echo "Pulling database and avatar index file..."
		adb pull $MM_DIR/MicroMsg/$chooseUser/EnMicroMsg.db
		[[ -f EnMicroMsg.db ]] && \
			echo "Database successfully downloaded to EnMicroMsg.db" || {
			>&2 echo "Failed to pull database by adb"
			exit 1
		}
		adb pull $MM_DIR/MicroMsg/$chooseUser/sfs/avatar.index
		[[ -f avatar.index ]] && \
			echo "Avatar index successfully downloaded to avatar.index" || {
				>&2 echo "Failed to pull avatar index by adb, are you using latest version of wechat?"
				exit 1
			}
	fi
elif [[ $1 == "db-decrypt" ]]; then
	set -e
	echo "Getting uin..."
	$0 uin | tail -n1 | $GREP -o '\-?[0-9]*' | tee /tmp/uin
	echo "Getting imei..."
	$0 imei | tail -n1 | $GREP -o '[0-9]*' | tee /tmp/imei
	echo "Getting db..."
	$0 db
	echo "Decrypting db..."
	imei=$(cat /tmp/imei)
	uin=$(cat /tmp/uin)
	if [[ -z $imei || -z $uin ]]; then
		>&2 echo "Failed to get imei or uin. See README for manual methods."
		exit 1
	fi
	./decrypt-db.py EnMicroMsg.db $imei $uin
	rm /tmp/{uin,imei}
	echo "Done. See decoded.db"
else
	echo "Usage: $0 <res|db-decrypt>"
	exit 1
fi

