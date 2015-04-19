## Dump WeChat Messages from Android

WeChat(微信), as the most popular mobile IM app in China, failed to allow users to export well-formatted chat history.
This tool can parse and dump WeChat chat history on a rooted android phone.

### How to use:

#### Dependencies:
+ python-PIL
+ [PyQuery](https://pypi.python.org/pypi/pyquery/1.2.1)
+ [pysox](https://pypi.python.org/pypi/pysox/0.3.6.alpha)
+ [dill](https://pypi.python.org/pypi/dill)
+ python-csscompressor(optional)
+ adb and rooted android phone connected to PC

#### Get Necessary Data:
+ Get decrypted WeChat database (Linux & Mac Only):
	+ Automatic: `./android-interact.sh db_decrypt`
	+ Manual:
		+ Get /data/data/com.tencent.mm/MicroMsg/long-long-name/EnMicroMsg.db from *root* filesystem, possible ways are:
			+ `./android-interact.sh db`
			+ Use your rooted file system manager app
		+ Get WeChat uin, possible ways are:
			+ `./android-interact.sh uin`
			+ Login to [web wechat](https://wx.qq.com), get wxuin=1234567 from `document.cookie`
		+ Get your phone IMEI number, possible ways are:
			+ `./android-interact.sh imei`
			+ Call `*#06#` on your phone
			+ Find IMEI in system settings
		+ Decrypt database, will produce `decrypted.db`:
		```
		./decrypt_db.sh <path to EnMicroMsg.db> <imei> <uin>
		```
+ Get WeChat user resource directory from your phone to `resource` directory:
	+ `./android-interact.sh res`		# you might need to change the resource location in this script if the default doesn't work

#### Run:
+ Parse and dump text messages of every contact (resource directory is not required to run this):
```
./dump_msg.py decrypted.db output_dir
```
+ Dump messages of one contact to rich-content html, containing voice messages, emojis, and images:
```
./dump_html.py decrypted.db resource <contact name> output.html
```
+ Generate statistical report on text messages:
```
./report.sh message_dir
```
### Examples:
See [here](http://ppwwyyxx.com/static/wechat/example.html) for an example html.

Screenshots:

![byvoid](https://github.com/ppwwyyxx/wechat-dump/raw/master/screenshots/byvoid.jpg)

### TODO
+ (IMPORTANT) Audio file encryption method for latest version of wechat.
+ Export all messages to libchat, and render messages from libchat
+ Search by uid/username
+ Skip existing files when copying android resources
+ Fix rare unhandled types: > 10000 and < 0
+ Better user experiences... see `grep 'TODO' lib -R`
+ more easy-to-use for non-programmers (GUI?)

### Disclaimers
This tool is still under development and testing, therefore it might not work very well on every device.

Use this software at your own risk. The author is not responsible for any potential damage/loss/privacy
issues related to the use of this tool.
