## Dump Wechat Messages from Android

### How to use:

#### Install Dependencies:
+ numpy
+ PIL
+ audioread
+ sox

#### Get Necessary Data:
+ Get /data/data/com.tencent.mm/MicroMsg/long-long-name/EnMicroMsg.db from rooted phone:
+ Get Wechat resource directory, usually at storage:/tencent/MicroMsg/long-long-name
+ Get Wechat uin:
	+ login to [web-based wechat](https://wx.qq.com); get wxuin=1234567 from `document.cookie`
	+ Or get ``default_uin`` from /data/data/com.tencent.mm/shared_prefs/system_config_prefs.xml.
+ Get phone IMEI:
	+ Call `*#06#` on your phone
	+ Or find IMEI in system settings
	+ Or use `adb shell dumpsys iphonesubinfo | grep 'Device ID' | grep -o '[0-9]*'`

#### Run:
+ Decrypt database and get decrypted_db.db (for now, Linux x64 only):
```
./decrypt_db.sh <path to EnMicroMsg.db> <imei> <uin>
```
+ Parse and dump text messages of every contact:
```
./dump_msg.py decrypted_db.db output_dir
```
+ Dump messages of one contact to html (for now, raw message only):
```
./dump_html.py decrypted_db.db <resource directory> <contact name> output.html
```

### TODO
+ parse audio messages, links, emoji and images
+ output to rich-content html
