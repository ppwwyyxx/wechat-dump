#!/bin/bash
# File: android-interact.sh

PROG_NAME=`python -c "import os, sys; print(os.path.realpath(sys.argv[1]))" "$0"`
PROG_DIR=`dirname "$PROG_NAME"`
cd "$PROG_DIR"

# Please check that your path is the same, since this might be different among devices
# RES_DIR="/mnt/sdcard/tencent/MicroMsg"  # old version of wechat use this path.
RES_DIR="/data/data/com.tencent.mm/MicroMsg"

if [[ $1 == "db" || $1 == "res" ]]; then
	echo "Looking for user dir name..."
	# look for dirname which looks like md5 (32 alpha-numeric chars)
	userList=$(adb shell su -c "ls $RES_DIR" | awk '{if (length() == 32) print}')
	numUser=$(echo "$userList" | wc -l)
	# choose the first user.
	chooseUser=$(echo "$userList" | head -n1)
	[[ -n $chooseUser ]] || {
		>&2 echo "Could not find user. Please check whether your resource dir is $RES_DIR"
		exit 1
	}
	echo "Found $numUser user(s). User chosen: $chooseUser"

	if [[ $1 == "res" ]]; then
		mkdir -p resource
    (
      cd resource || exit
      echo "Pulling resources... "
      for d in avatar image2 voice2 emoji video sfs; do
        echo "Trying to download $RES_DIR/$chooseUser/$d with busybox ..."
        adb shell su -c "busybox tar czf - $RES_DIR/$chooseUser/$d 2>/dev/null |
			busybox base64" | base64 -di | tar xzf - --strip-components 5
        [[ -d $d ]] && continue

        echo "Trying to download $RES_DIR/$chooseUser/$d with tar & base64 ..."
        adb shell su -c "tar czf - $RES_DIR/$chooseUser/$d 2>/dev/null | base64" |
			base64 -di | tar xzf - --strip-components 5
        [[ -d $d ]] && continue

        echo "Trying to download $RES_DIR/$chooseUser/$d with adb pull (slow) ..."
        mkdir -p $d
        (
          cd $d || exit
		  adb root
		  sleep 1 # sometimes adb complains: device not found
          adb pull "$RES_DIR/$chooseUser/$d"
        )

        [[ -d $d ]] || {
          echo "Failed to download $RES_DIR/$chooseUser/$d"
        }
      done
      echo "Resource pulled at ./resource"
      echo "Total size: $(du -sh | cut -f1)"
    )
	else
	  for f in EnMicroMsg.db sfs/avatar.index; do
		echo "Trying to download $RES_DIR/$chooseUser/$f with busybox ..."
		adb shell su -c "busybox tar czf - $RES_DIR/$chooseUser/$f 2>/dev/null |
			busybox base64" | base64 -di | tar xzf - --strip-components 5
		[[ -f $f ]] && continue

		echo "Trying to download $RES_DIR/$chooseUser/$f with tar & base64 ..."
		adb shell su -c "tar czf - $RES_DIR/$chooseUser/$f 2>/dev/null | base64" |
			base64 -di | tar xzf - --strip-components 5
		[[ -f $f ]] && continue

		echo "Trying to download $RES_DIR/$chooseUser/$f with adb pull..."
		adb root
		sleep 1
		adb pull $RES_DIR/$chooseUser/$f

		[[ -f $f ]] || {
			echo "Failed to download $RES_DIR/$chooseUser/$f"
		}
	  done
	  echo "Database and avatar index file successfully downloaded"
	fi
else
	echo "Usage: $0 <res|db>"
	exit 1
fi
