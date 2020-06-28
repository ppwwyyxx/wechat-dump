## Dump WeChat Messages from Android

## 导出安卓微信聊天数据

WeChat(微信), as the most popular mobile IM app in China, doesn't give users any method to export well-formatted history message.
This tool can parse and export WeChat messages on a rooted android phone.

Right now it can dump messages in text-only mode, or generate a single-file html containing voice messages, images, emoji, etc.

If this tools works for you, please take a moment to __add your phone/OS to__ [the wiki](https://github.com/ppwwyyxx/wechat-dump/wiki).
If it doesn't work, you probably have to investigate it as the behavior may be different on each phone.

### How to use:

#### Dependencies:
+ adb and rooted android phone connected to a Linux/Mac OSX/Win10+Bash.
  If the phone does not come with adb support, you can download an app such as https://play.google.com/store/apps/details?id=eu.chainfire.adbd
+ Python >= 3.6
+ [PyQuery](https://pypi.python.org/pypi/pyquery/), [javaobj-py3](https://pypi.org/project/javaobj-py3), Pillow, requests
+ [sqlcipher](https://github.com/sqlcipher/sqlcipher) >= 4.1, [pysqlcipher3](https://pypi.python.org/pypi/pysqlcipher3)
+ sox, openssl (command line tools)
+ csscompressor (suggested, optional)
+ Silk audio decoder (included; build with `./third-party/compile_silk.sh`)

#### Get Necessary Data:

1. Pull database file and avatar index:
  + Automatic: `./android-interact.sh db`. It may use an incorrect userid.
  + Manual:
    + Figure out your `${userid}` by inspecting the contents of `/data/data/com.tencent.mm/MicroMsg` on the __root__ filesystem of the device. It should be a 32-character-long name consisting of hexadecimal digits.
    + Get `/data/data/com.tencent.mm/MicroMsg/${userid}/{EnMicroMsg.db,sfs/avatar.index}` from the device.
2. Decrypt database file:
  + Automatic: `./decrypt-db.py decrypt --input EnMicroMsg.db`
  + Manual:
    + Get WeChat uin (an integer), possible ways are:
      + `./decrypt-db.py uin`, which looks for uin in `/data/data/com.tencent.mm/shared_prefs/`
      + Login to [web wechat](https://wx.qq.com), get wxuin=1234567 from `document.cookie`
    + Get your device id (a positive integer), possible ways are:
      + `./decrypt-db.py imei` implements some ways to find device id.
      + Call `*#06#` on your phone
      + Find IMEI in system settings
    + Decrypt database with combination of uin and device id:

      ```
      ./decrypt-db.py decrypt --input EnMicroMsg.db --imei <device id> --uin <uin>
      ```

      NOTE: you may need to try different ways to get device id and fine one that can decrypt the
      database. Some phones may have multiple IMEIs, you may need to try them all.
      See [#33](https://github.com/ppwwyyxx/wechat-dump/issues/33).
      The command will dump decrypted database at `EnMicroMsg.db.decrypted`.

  If decryption doesn't work, you can also try the [password cracker](https://github.com/chg-hou/EnMicroMsg.db-Password-Cracker)
  to brute-force the password.

3. Copy the WeChat user resource directory `/mnt/sdcard/tencent/MicroMsg/${userid}/{avatar,emoji,image2,sfs,video,voice2}` from the phone to the `resource` directory:
	+ `./android-interact.sh res`
	+ You might need to change `RES_DIR` in the script if the default is incorrect on your phone.
	+ This can take a while. One way that might be slightly faster:
    + If there's enough free space on your phone, you can log in and archive all required files via `tar` with or without compression,
		  and use `adb pull` to copy the archive. Note that `busybox tar` is recommended as the Android system's `tar` may choke on long paths.
	+ What is needed in the end is a `resource` directory with the following subdir: `avatar,emoji,image2,sfs,video,voice2`.

4. (Optional) Download the emoji cache from [here](https://github.com/ppwwyyxx/wechat-dump/releases/download/0.1/emoji.cache.tar.bz2)
	and decompress it under `wechat-dump`. This will avoid downloading too many emojis during rendering.

        wget -c https://github.com/ppwwyyxx/wechat-dump/releases/download/0.1/emoji.cache.tar.bz2
        tar xf emoji.cache.tar.bz2

#### Run:
+ Parse and dump text messages of __every__ chat (requires decrypted database):

    ```
    ./dump-msg.py decrypted.db output_dir
    ```

+ List all chats (required decrypted database):

    ```
    ./list-chats.py decrypted.db
    ```

+ Generate statistics report on text messages (requires `output_dir` from `./dump-msg.py`):

    ```
    ./count-message.sh output_dir
    ```

+ Dump messages of one contact to html, containing voice messages, emojis, and images (requires decrypted database, `avatar.index`, and `resource`):

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
+ Crack emoji encryption to handle some missing emojis.
  * __HELP WANTED__: Starting from May 2016, the first 1KB of all emojis in `resource/emoji` are encrypted. Right now I'm using emoji URL which covers most of them.
    Any thoughts on how they are encrypted are appreciated.
    It is also possible to recover the image without knowing the first 1KB (just have to detect chunks without knowing metadata).
+ Fix rare unhandled message types: > 10000 and < 0
+ Better user experiences... see `grep 'TODO' wechat -R`


### Donate!
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=7BC299GRDLEDU&lc=US&item_name=wechat%2ddump&item_number=wechat%2ddump&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted">
<img src="https://img.shields.io/badge/Paypal-Buy%20a%20Drink-blue.svg" alt="[paypal]" />
</a>
