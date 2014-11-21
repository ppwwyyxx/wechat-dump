## Dump Wechat Messages from Android

### How to use (for now, Linux x64 only):

+ Get /data/data/com.tencent.mm/MicroMsg/long-long-name/EnMicroMsg.db from rooted phone:
+ Get wechat uin:
	1. log on [web-based wechat](https://wx.qq.com)
	2. get wxuin=1234567 from `document.cookie`
+ Get phone IMEI:
	+ Call `*#06#` on your phone
	+ Or find IMEI in system settings
	+ Or use `adb shell dumpsys iphonesubinfo`
+ Decrypt database and get decrypted_database.db:
```
./decrypt_db.sh <path to EnMicroMsg.db> <imei> <uin>
```
+ Parse and dump messages:
```
./dump_msg.py decrypted_database.db output_dir
```

### TODO
+ parse audio messages, links, emoji and images
+ output to rich-content html
