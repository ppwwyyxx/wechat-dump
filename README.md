## Dump WeChat Messages from Android

## 导出安卓微信聊天数据

WeChat(微信), as the most popular mobile IM app in China, doesn't give users any method to export well-formatted history message.
This tool can parse and export WeChat messages on a rooted android phone.

Right now it can dump messages in text-only mode, or generate a single-file html containing voice messages, images, emoji, etc.

__NEWS__: WeChat 6.0+ uses silk to encode audio. The code is updated.

__NEWS__: WeChat 6.3 uses a new avatar storage. The code is updated.

If this tools works for you, please take a moment to __add your phone/OS to__ [the wiki](https://github.com/ppwwyyxx/wechat-dump/wiki).
If it doesn't work, please leave an issue together with your phone/OS/wechat version.

### How to use:

#### Dependencies:
+ python-PIL
+ [PyQuery](https://pypi.python.org/pypi/pyquery/1.2.1)
+ [pysox](https://pypi.python.org/pypi/pysox/0.3.6.alpha)
+ [pysqlcipher](https://pypi.python.org/pypi/pysqlcipher)
+ numpy
+ csscompressor (suggested, optional)
+ adb and rooted android phone connected to a Linux/Mac OS.
+ Silk audio decoder (included; just run `./third-party/compile_silk.sh`)
+ gnu-sed

#### Get Necessary Data:

Note that commands involving `./android-interact.sh` are meant to be run on the computer.

+ (Requires Linux or Mac) Get the decrypted WeChat database and the avatar index:
	+ Automatic: `./android-interact.sh db-decrypt`
		+ Requires rooted adb. If the OS distribution does not come with adb support, you can download an app such as https://play.google.com/store/apps/details?id=eu.chainfire.adbd
	+ Manual:
		+ Figure out your `${userid}` by inspecting the contents of `/data/data/com.tencent.mm/MicroMsg` on the __root__ filesystem of the device. It should be a 32-character-long name consisting of hexadecimal digits.
		+ Get `/data/data/com.tencent.mm/MicroMsg/${userid}/{EnMicroMsg.db,sfs/avatar.index}` from the device, possible ways are:
			+ `./android-interact.sh db`
			+ Use your rooted file system manager app
		+ Get WeChat uin (an integer), possible ways are:
			+ `./android-interact.sh uin`, which pulls the value from `/data/data/com.tencent.mm/shared_prefs/system_config_prefs.xml`
			+ Login to [web wechat](https://wx.qq.com), get wxuin=1234567 from `document.cookie`
		+ Get your phone IMEI number (a positive integer), possible ways are:
			+ `./android-interact.sh imei`
			+ Call `*#06#` on your phone
			+ Find IMEI in system settings
		+ Decrypt database, will produce `decrypted.db`:

            ```
            ./decrypt-db.py <path to EnMicroMsg.db> <imei> <uin>
            ```

    NOTE: you may need to try different ways to getting imei & uin,
    because things behave differently on different phones.

    Also, if the decryption doesn't work with pysqlcipher, maybe try the version of sqlcipher in `legacy`.


+ Copy the WeChat user resource directory `/mnt/sdcard/tencent/MicroMsg/${userid}/{emoji,image2,sfs,video,voice2}` from the phone's SD card to the `resource` directory:
	+ `./android-interact.sh res`
	+ You might need to tweak `RES_DIR` in the script if the default doesn't work
	+ This can take a __long__ time. Some ways to do this faster:
        + If there's enough free space on the SD card, you can combine all the files via `busybox tar` without compression in the `adb shell`, use `adb pull` to copy the `tar` archive to the computer, and then extract it. BusyBox is needed as the Android system's `tar` may choke on long paths.
        + Alternatively, you can use pipes.  This is slower, but doesn't require any free space on the SD card:

            ```sh
            # copy MicroMsg to the current directory
            adb shell 'cd /mnt/sdcard/tencent &&
                       busybox tar czf - MicroMsg 2>/dev/null | busybox base64' |
                base64 -di | tar xzf -
            ```

#### Run:
+ Parse and dump text messages of __every__ chat (requires `decrypted.db`):

    ```
    ./dump-msg.py decrypted.db output_dir
    ```

+ List all chats (requires `decrypted.db`):

    ```
    ./list-chats.py decrypted.db
    ```

+ Generate statistical report on text messages (requires `output_dir` from `./dump-msg.py`):

    ```
    ./count-message.sh output_dir
    ```

+ Dump messages of one contact to html, containing voice messages, emojis, and images (requires `decrypted.db`, `avatar.index`, and `resource`):

    ```
    ./dump-html.py decrypted.db avatar.index resource "<contact_name>" output.html
    ```

### Examples:
See [here](http://ppwwyyxx.com/static/wechat/example.html) for an example html.

Screenshots of generated html:

![byvoid](https://github.com/ppwwyyxx/wechat-dump/raw/master/screenshots/byvoid.jpg)

### TODO List
+ Search by uid/username
+ Faster way to copy a directory from android (I don't know..).
+ Fix rare unhandled types: > 10000 and < 0
+ Better user experiences... see `grep 'TODO' wechat -R`
+ more easy-to-use for non-programmers (GUI?)

### Donate!
Paypal:
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=7BC299GRDLEDU&lc=US&item_name=wechat%2ddump&item_number=wechat%2ddump&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted">
<img src="https://img.shields.io/badge/Paypal-Buy%20a%20Drink-blue.svg" alt="[paypal]" />
</a>
