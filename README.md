## Dump WeChat Messages from Android

## 导出安卓微信聊天数据

WeChat(微信), as the most popular mobile IM app in China, failed to allow users to export well-formatted chat history.
This tool can parse and export WeChat message history on a rooted android phone.

It can generate single-file html containing all the messages, including voice message, image, emoji, etc.

__NEWS__: WeChat 6.0+ use silk to encode audio. The code is updated.

### How to use:

#### Dependencies:
+ python-PIL
+ [PyQuery](https://pypi.python.org/pypi/pyquery/1.2.1)
+ [pysox](https://pypi.python.org/pypi/pysox/0.3.6.alpha)
+ numpy
+ python-csscompressor(optional)
+ adb and rooted android phone connected to PC
+ gnu-sed
+ Silk audio decoder (just run `./third-party/compile_silk.sh`)

#### Get Necessary Data:

+ Get decrypted WeChat database (Linux & Mac Only):
	+ Automatic: `./android-interact.sh db-decrypt`
		+ Requires rooted adb. Available at https://play.google.com/store/apps/details?id=eu.chainfire.adbd&hl=en
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
		./decrypt-db.sh <path to EnMicroMsg.db> <imei> <uin>
		```

NOTE: you may need to try different ways to getting imei & uin,
because things behave differently on different phones.


+ Get WeChat user resource directory from your phone to `resource` directory:
	+ `./android-interact.sh res`
	+ You might need to change the resource location in this script if the default doesn't work
	+ This takes a long time.

#### Run:
+ Parse and dump text messages of every contact (resource directory is not required to run this):
```
./dump-msg.py decrypted.db output_dir
```
+ Dump messages of one contact to rich-content html, containing voice messages, emojis, and images:
```
./dump-html.py decrypted.db resource <contact name> output.html
```
+ Generate statistical report on text messages:
```
./count-message.sh message_dir
```
### Examples:
See [here](http://ppwwyyxx.com/static/wechat/example.html) for an example html.

Screenshots of generated html:

![byvoid](https://github.com/ppwwyyxx/wechat-dump/raw/master/screenshots/byvoid.jpg)

### TODO
+ Use libchat as unified backend. Export all messages to libchat, and render messages from libchat
+ Search by uid/username
+ Skip existing files when copying android resources
+ Fix rare unhandled types: > 10000 and < 0
+ Use alias name in group chat, instead of id
+ Better user experiences... see `grep 'TODO' wechat -R`
+ more easy-to-use for non-programmers (GUI?)

### Donate!
Paypal:
<form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
<input type="hidden" name="cmd" value="_s-xclick">
<input type="hidden" name="encrypted" value="-----BEGIN PKCS7-----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-----END PKCS7-----
">
<input type="image" src="https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif" border="0" name="submit" alt="PayPal - The safer, easier way to pay online!">
<img alt="" border="0" src="https://www.paypalobjects.com/en_US/i/scr/pixel.gif" width="1" height="1">
</form>

Alipay:
<form action="https://shenghuo.alipay.com/send/payment/fill.htm" method="POST" target="_blank" accept-charset="GBK">
	<input name="optEmail" type="hidden" value="ppwwyyxxc@gmail.com" />
	<input id="title" name="title" type="hidden" value="wechat-dump" />
	<input name="pay" type="image" value="轉賬" src="https://img.alipay.com/sys/personalprod/style/mc/btn-index.png" width="100"/>
</form>
