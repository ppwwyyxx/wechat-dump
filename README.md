## Dump WeChat Messages from Android

## 导出安卓微信消息记录

WeChat, as the most popular mobile IM app in China, doesn't provide any methods to export structured message history.

We reverse-engineered the storage protocol of WeChat messages, and
provide this tool to decrypt and parse WeChat messages on a rooted android phone.
It can also render the messages into self-contained html files including voice messages, images, emojis, videos, etc.

The tool is last verified to work with latest version of WeChat on 2025/01/01.
If the tool works for you, please take a moment to add your phone/OS to [the wiki](https://github.com/ppwwyyxx/wechat-dump/wiki).

## How to use:

#### Dependencies:
+ adb and rooted android phone connected to a Linux/Mac OSX/Win10+Bash.
+ Python >= 3.8
+ [sqlcipher](https://github.com/sqlcipher/sqlcipher) >= 4.1
+ sox (command line tools)
+ Silk audio decoder (included; build it with `./third-party/compile_silk.sh`)
+ Other python dependencies: `pip install -r requirements.txt`.

#### Get Necessary Data:

1. Pull database file and (for older WeChat versions) avatar index:
  + Automatic: `./android-interact.sh db`. It may use an incorrect userid.
  + Manual:
    + Figure out your `${userid}` by inspecting the contents of `/data/data/com.tencent.mm/MicroMsg` on the __root__ filesystem of the device.
      It should be a 32-character-long name consisting of hexadecimal digits.
    + Get `/data/data/com.tencent.mm/MicroMsg/${userid}/EnMicroMsg.db` from the device.
2. Decrypt database file:
  + Automatic: `./decrypt-db.py decrypt --input EnMicroMsg.db`
  + Manual:
    + Get WeChat uin (an integer), possible ways are:
      + `./decrypt-db.py uin`, which looks for uin in `/data/data/com.tencent.mm/shared_prefs/`
      + Login to [web WeChat](https://wx.qq.com), get wxuin=1234567 from `document.cookie`
    + Get your device id (a positive integer), possible ways are:
      + `./decrypt-db.py imei` implements some ways to find device id.
      + Call `*#06#` on your phone
      + Find IMEI in system settings
    + Decrypt database with combination of uin and device id:

      ```
      ./decrypt-db.py decrypt --input EnMicroMsg.db --imei <device id> --uin <uin>
      ```

      NOTE: you may need to try different ways to get device id and find one that can decrypt the
      database. Some phones may have multiple IMEIs, you may need to try them all.
      See [#33](https://github.com/ppwwyyxx/wechat-dump/issues/33).
      The command will dump decrypted database at `EnMicroMsg.db.decrypted`.

  If the above decryption doesn't work, you can also try the [password cracker](https://github.com/chg-hou/EnMicroMsg.db-Password-Cracker)
  to brute-force the key. The encryption key is not very strong.

3. Copy the WeChat user resource directory `/data/data/com.tencent.mm/MicroMsg/${userid}/{avatar,emoji,image2,sfs,video,voice2}` from the phone to the `resource` directory:
	+ `./android-interact.sh res`
	+ Change `RES_DIR` in the script if the location of these directories is different on your phone.
      For older version of WeChat, the directory may be `/mnt/sdcard/tencent/MicroMsg/`
	+ This can take a while. It can be faster to first archive it with `tar` with or without compression, and then copy the archive,
  	  `busybox tar` is recommended as the Android system's `tar` may choke on long paths.
	+ In the end, we need a `resource` directory with the following subdir: `avatar,emoji,image2,sfs,video,voice2`.

4. (Optional) Install and start a WXGF decoder server on an android device. Without this, certain WXGF images will not be rendered or will be rendered in low resolution.
   See [WXGFDecoder](WXGFDecoder) for instructions.

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

+ Dump messages of one contact to html, containing voice messages, emojis, and images (requires decrypted database and `resource`):

    ```
    ./dump-html.py "<contact_display_name>"
    ```

    * The output file is `output.html`. Check `./dump-html.py -h` to use different input/output paths.
    * Add `--wxgf-server ws://xx.xx.xx.xx:xxxx` to use a WXGF decoder server.

### Examples:
Screenshots of generated html:

![byvoid](https://github.com/ppwwyyxx/wechat-dump/raw/master/screenshots/byvoid.jpg)

See [here](http://ppwwyyxx.com/static/wechat/example.html) for an example html.

### TODO List (help needed!)
* After chat history migration, some emojis in the `EmojiInfo` table don't have corresponding URLs but only a md5 -
  they are not downloaded by WeChat until the message needs to be displayed. We don't know how to manually download these emojis.
* Decoding WXGF images using an android app is too complex. Looking for an easier way (e.g. qemu).
* Fix rare unhandled message types: > 10000 and < 0
* Better user experiences... see `grep 'TODO' wechat -R`

### Donate!
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=7BC299GRDLEDU&lc=US&item_name=wechat%2ddump&item_number=wechat%2ddump&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted">
<img src="https://img.shields.io/badge/Paypal-Buy%20a%20Drink-blue.svg" alt="[paypal]" />
</a>
