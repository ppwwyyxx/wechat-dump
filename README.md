## Dump WeChat Messages from Android

## 导出安卓微信聊天数据

WeChat(微信), as the most popular mobile IM app in China, doesn't give users any method to export well-formatted history message.
This tool can parse and export WeChat messages on a rooted android phone.

Right now it can dump messages in text-only mode, or generate a single-file html containing voice messages, images, emoji, etc.

__NEWS__: WeChat 6.0+ uses silk to encode audio. The code is updated.

__NEWS__: WeChat 6.3 uses a new avatar storage. The code is updated.

__HELP NEEDED__: Starting from May 2016, the first 1KB of all emojis in `resource/emoji` are encrypted. Right now I'm using emoji URL which covers most of them.

If you are good at cryptography / reverse engineereing, or you work at Tencent, feel free to contact me or help take a look.
It is also possible to recover the image without knowing the first 1KB (just have to detect chunks without knowing metadata), but I don't have time to do that either.

If this tools works for you, please take a moment to __add your phone/OS to__ [the wiki](https://github.com/ppwwyyxx/wechat-dump/wiki).
If it doesn't work, please leave an issue together with your phone/OS/wechat version.

### How to use:

#### Dependencies:

+ requests
+ python-PIL
+ [PyQuery](https://pypi.python.org/pypi/pyquery/1.2.1)
+ [pysox](https://pypi.python.org/pypi/pysox/0.3.6.alpha) and sox
+ [pysqlcipher](https://pypi.python.org/pypi/pysqlcipher)
+ numpy
+ csscompressor (suggested, optional)
+ adb and rooted android phone connected to a Linux/Mac OSX/Win10+Bash.
+ Silk audio decoder (included; just run `./third-party/compile_silk.sh`)
+ gnu-sed

On Debian/Ubuntu systems, these dependencies can be installed via:

```sh
sudo apt-get install sox android-tools-adb python-requests python-pil python-pyquery python-numpy libsox-dev libsqlite3-dev libsqlcipher-dev
pip install --user pysqlcipher csscompressor
pip install --user --pre pysox
```

#### Get Necessary Data:

+ Get the decrypted WeChat database and the avatar index:
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
		+ Get your phone IMEI/MEID number (a positive integer), possible ways are:
			+ `./android-interact.sh imei`
			+ Call `*#06#` on your phone
			+ Find IMEI in system settings
		+ Decrypt database, will produce `decrypted.db`:

            ```
            ./decrypt-db.py <path to EnMicroMsg.db> <imei> <uin>
            ```

    NOTE: you may need to try different ways to get IMEI/MEID,
		because things behave differently on different phones.
		Some phones may have multiple IMEIs, you may need to try them all.
		See [#33](https://github.com/ppwwyyxx/wechat-dump/issues/33).

		If decryption doesn't work, you can also try the [password cracker](https://github.com/chg-hou/EnMicroMsg.db-Password-Cracker)
		to brute-force the password.

+ Copy the WeChat user resource directory `/mnt/sdcard/tencent/MicroMsg/${userid}/{avatar,emoji,image2,sfs,video,voice2}` from the phone to the `resource` directory:
	+ `./android-interact.sh res`
	+ You might need to change `RES_DIR` in the script if the default is incorrect on your phone.
	+ This script needs busybox and base64 on your phone.
		If they are not available, there is a slow fallback method in the script you can use.
	+ This can take a few minutes. One way to do it faster:
        + If there's enough free space on your phone, you can log in and archive all required files via `busybox tar` with or without compression,
				and use `adb pull` to copy the archive. Note that `busybox` is needed as the Android system's `tar` may choke on long paths.
	+ What you'll need in the end is a `resource` directory with the following subdir: `avatar,emoji,image2,sfs,video,voice2`.

+ (Optional) Download the emoji cache from [here](https://github.com/ppwwyyxx/wechat-dump/releases/download/0.1/emoji.cache.tar.bz2)
	and decompress it under `wechat-dump`. This will avoid downloading too many emojis during rendering.

        wget -c https://github.com/ppwwyyxx/wechat-dump/releases/download/0.1/emoji.cache.tar.bz2
        tar xf emoji.cache.tar.bz2

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
    ./dump-html.py "<contact_display_name>"
    ```

    The output file is `output.html`.

    Check `./dump-html.py -h` to use different paths.

### Examples:
Screenshots of generated html:

![byvoid](https://github.com/ppwwyyxx/wechat-dump/raw/master/screenshots/byvoid.jpg)

See [here](http://ppwwyyxx.com/static/wechat/example.html) for an example html.

### TODO List
+ Attack the emoji encryption problem
+ Use pipes by default to copy a directory from android
+ Fix rare unhandled message types: > 10000 and < 0
+ Better user experiences... see `grep 'TODO' wechat -R`


### Donate!
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=7BC299GRDLEDU&lc=US&item_name=wechat%2ddump&item_number=wechat%2ddump&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted">
<img src="https://img.shields.io/badge/Paypal-Buy%20a%20Drink-blue.svg" alt="[paypal]" />
</a>
