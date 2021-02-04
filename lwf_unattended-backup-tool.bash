#!/bin/bash -x

declare UIN
declare IMEI
declare DATA_ID
declare SDCARD_ID

OUTPUT_DIR=/home/lockywolf/BACKUP/08_Chat-Logs/004_WeChat
SOURCE_DIR=/home/lockywolf/OfficialRepos/wechat-dump

source "$OUTPUT_DIR/lwf_unattended-backup-tool.bash.conf" || exit 1

set -eo pipefail

printf "hello\n"
LAST_CHECK=$(cat $OUTPUT_DIR/LAST_CHECK)
LAST_CHECK=${LAST_CHECK:-0}

echo $LAST_CHECK

NOW=$(date +"%s")
printf "Now is %s\n" "$NOW"
printf "%s" "$NOW" > "$OUTPUT_DIR/LAST_CHECK"

NOW_TEXT=$(date --date=@$NOW)
printf "That is %s\n" "$NOW_TEXT"
SNAPSHOT_DIR_NAME=$(date --date=@$NOW +%Y-%m-%d)
printf "Making dir %s\n" "$SNAPSHOT_DIR_NAME"
NEW_CWD="$OUTPUT_DIR"/"$SNAPSHOT_DIR_NAME"
mkdir "$NEW_CWD" || exit 1
cd "$NEW_CWD"
pwd


mkdir -p resource
adb shell "mkdir -p /sdcard/locky_backup" || exit 1
adb shell su -c "cp /data/data/com.tencent.mm/MicroMsg/$DATA_ID/EnMicroMsg.db /sdcard/locky_backup/" || exit 1
adb pull "/sdcard/locky_backup/EnMicroMsg.db" || exit 1

# Collect resources.
#{avatar,emoji,image2,sfs,video,voice2}

adb shell su -c "cp -r /data/data/com.tencent.mm/MicroMsg/$DATA_ID/image2 /sdcard/locky_backup/" || exit 1

adb shell su -c "cp -r /data/data/com.tencent.mm/MicroMsg/$DATA_ID/avatar /sdcard/locky_backup/" || exit 1


adb pull "/sdcard/locky_backup/image2" || exit 1
adb pull "/sdcard/locky_backup/avatar" || exit 1

adb shell "rm -rf /sdcard/locky_backup/image2" || exit 1
adb shell "rm -rf /sdcard/locky_backup/avatar" || exit 1
adb shell "rm /sdcard/locky_backup/EnMicroMsg.db" || exit 1

mv image2  resource/
mv avatar resource/

pushd resource
#adb pull "/sdcard/Android/data/com.tencent.mm/MicroMsg/$SDCARD_ID/avatar/" || exit 1
#adb pull "/sdcard/Android/data/com.tencent.mm/MicroMsg/$SDCARD_ID/image2/" || exit 1

adb pull "/sdcard/Android/data/com.tencent.mm/MicroMsg/$SDCARD_ID/emoji/" || exit 1
adb pull "/sdcard/Android/data/com.tencent.mm/MicroMsg/$SDCARD_ID/video/" || exit 1
adb pull "/sdcard/Android/data/com.tencent.mm/MicroMsg/$SDCARD_ID/voice2/" || exit 1
ls
popd

source "$SOURCE_DIR/2021-02-02_python39-virtualenv/bin/activate"
"$SOURCE_DIR/decrypt-db.py" decrypt --input EnMicroMsg.db --imei "$IMEI" --uin "$UIN"


mkdir -p output_dir || exit 1
"$SOURCE_DIR/dump-msg.py" EnMicroMsg.db.decrypted output_dir || exit 1

"$SOURCE_DIR/dump-html.py" --db EnMicroMsg.db.decrypted "提么, carol okcupid"

mkdir output_dir_html || exit 1
pushd output_dir

readarray  USER_NAMES  < <(file ./* | grep text | cut -d ':' -f 1)

popd
for usern in "${USER_NAMES[@]}"
do
    USERNAME="${usern:2:-5}"
    "$SOURCE_DIR/dump-html.py" "$USERNAME" --db EnMicroMsg.db.decrypted --output "output_dir_html/$USERNAME".html || true
done

ls output_dir_html

ls



exit 1
