## Dump Wechat Messages from Android

### How to use:

#### Install Dependencies:
+ python-PIL
+ [PyQuery](https://pypi.python.org/pypi/pyquery/1.2.1)
+ pysox(https://pypi.python.org/pypi/pysox/0.3.6.alpha)
+ python-csscompressor(optional)

#### Get Necessary Data:
+ Get /data/data/com.tencent.mm/MicroMsg/long-long-name/EnMicroMsg.db from root filesystem, possible ways are:
	+ `./android-interact.sh db`
	+ Use your rooted file system manager app
+ Get WeChat user resource directory from your phone:
	+ `./android-interact.sh res`		# you might need to specify a location if the default doesn't work
+ Get Wechat uin, possible ways are:
	+ `./android-interact.sh uin`
	+ Login to [web wechat](https://wx.qq.com), get wxuin=1234567 from `document.cookie`
+ Get phone IMEI, possible ways are:
	+ `./android-interact.sh imei`
	+ Call `*#06#` on your phone
	+ Find IMEI in system settings

#### Run:
+ Decrypt database, will produce decrypted_db.db (for now, Linux only):
```
./decrypt_db.sh <path to EnMicroMsg.db> <imei> <uin>
```
+ Parse and dump text messages of every contact:
```
./dump_msg.py decrypted_db.db output_dir
```
+ Dump messages of one contact to single-file html, containing voice messages and images:
```
./dump_html.py decrypted_db.db <resource directory> <contact name> output.html
```

### TODO
+ Group message
+ Change max size for custom emoji
+ Show name of emoji in text output
+ Search by uid/username..
