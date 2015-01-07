#!/bin/bash -e
# File: android-interact.sh
# Date: Wed Jan 07 21:57:59 2015 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>
PROG_NAME=`readlink -f "$0"`
PROG_DIR=`dirname "$PROG_NAME"`
cd "$PROG_DIR"

# Please check that your path is the same, since this might be different among devices
RES_DIR="/mnt/sdcard/tencent/MicroMsg"
MM_DIR="/data/data/com.tencent.mm"

echo "Starting rooted adb server..."
adb root

if [[ $1 == "uin" ]]; then
	adb pull $MM_DIR/shared_prefs/system_config_prefs.xml 2>/dev/null
	uin=$(grep 'default_uin' system_config_prefs.xml | grep -o 'value="[0-9]*' | cut -c 8-)
	[[ -n $uin ]] || {
		echo "Failed to get wechat uin. You can try other methods, or report a bug."
		exit 1
	}
	rm system_config_prefs.xml
	echo "Got wechat uin: $uin"
elif [[ $1 == "imei" ]]; then
	imei=$(adb shell dumpsys iphonesubinfo | grep 'Device ID' | grep -o '[0-9]*')
	[[ -n $imei ]] || {
		echo "Failed to get imei. You can try other methods, or report a bug."
		exit 1
	}
	echo "Got imei: $imei"
elif [[ $1 == "db" || $1 == "res" ]]; then
	echo "Looking for user dir name..."
	userList=$(adb ls $RES_DIR | cut -f 4 -d ' ' \
		| awk '{if (length() == 32) print}')
	numUser=$(echo $userList | wc -l)
	# choose the first user.
	chooseUser=$(echo $userList | head -n1)
	[[ -n $chooseUser ]] || {
		echo "Could not find user. Please check whether your resource dir is $RES_DIR"
		exit 1
	}
	echo "Found $numUser user(s). User chosen: $chooseUser"

	if [[ $1 == "res" ]]; then
		echo "Pulling resources... this might take a long time..."
		mkdir -p resource; cd resource
		for d in image2 voice2 emoji avatar video; do
			mkdir -p $d; cd $d
			adb pull $RES_DIR/$chooseUser/$d
			cd ..
			[[ -d $d ]] || {
				echo "Failed to download resource directory: $RES_DIR/$chooseUser/$d"
				exit 1
			}
		done
		cd ..
		echo "Resource pulled at ./resource"
		echo "Total size: $(du -sh resource | cut -f1)"
	else
		echo "Pulling database file..."
		adb pull $MM_DIR/MicroMsg/$chooseUser/EnMicroMsg.db
		[[ -f EnMicroMsg.db ]] && \
			echo "File successfully downloaded to EnMicroMsg.db" || {
			echo "Failed to pull database from adb"
			exit 1
		}
	fi
elif [[ $1 == "all" ]]; then
	echo "Getting uin..."
	$0 uin | tail -n1 | grep -o '[0-9]*' > /tmp/uin
	echo "Getting imei..."
	$0 imei | tail -n1 | grep -o '[0-9]*' > /tmp/imei
	echo "Getting db..."
	$0 db
	echo "Decrypting db..."
	./decrypt_db.sh EnMicroMsg.db $(</tmp/imei) $(</tmp/uin)
	rm /tmp/{uin,imei}
	echo "Getting res..."
	$0 res
	echo "Done"
else
	echo "Usage: $0 <imei|uin|db|res|all>"
	exit 1
fi

