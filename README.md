## Dump WeChat Messages from Android

WeChat(微信), as the most popular mobile IM app in China, failed to allow users to export well-formatted chat history.
This tool can parse and dump WeChat chat history on a rooted android phone.

### How to use:

#### Install Dependencies:
+ python-PIL
+ [PyQuery](https://pypi.python.org/pypi/pyquery/1.2.1)
+ [pysox](https://pypi.python.org/pypi/pysox/0.3.6.alpha)
+ python-csscompressor(optional)

#### Get Necessary Data:
+ Get /data/data/com.tencent.mm/MicroMsg/long-long-name/EnMicroMsg.db from *root* filesystem, possible ways are:
	+ `./android-interact.sh db`
	+ Use your rooted file system manager app
+ Get WeChat user resource directory from your phone:
	+ `./android-interact.sh res`		# you might need to change the resource location in this script if the default doesn't work
+ Get WeChat uin, possible ways are:
	+ `./android-interact.sh uin`
	+ Login to [web wechat](https://wx.qq.com), get wxuin=1234567 from `document.cookie`
+ Get your phone IMEI number, possible ways are:
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
+ Dump messages of one contact to rich-content html, containing voice messages, emojis, and images:
```
./dump_html.py decrypted_db.db <resource directory> <contact name> output.html
```

### TODO
+ Search by uid/username
+ Skip existing files when copying android resources
+ Fix unhandled types: > 10000 and < 0
+ Better user experiences... see TODOs

### Disclaimers
Use this software at your own risk. The author is not responsible for any potential damage/loss/privacy
issues related to the use of this tool.
