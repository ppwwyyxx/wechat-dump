# Obtain Database Password Using Frida

You can obtain the access password directly through Frida. If you can access your WeChat account, this method can directly obtain the correct database password. 

## Install
Install frida on your computer and download frida-server for your phone:
```
pip install frida frida-tools

VERSION=$(frida --version)
ARCH=arm64
wget https://github.com/frida/frida/releases/download/$VERSION/frida-server-$VERSION-android-$ARCH.xz
xz -d frida-server-$VERSION-android-$ARCH.xz
```

* Note: if your device architecture is not arm64-v8a, replace "arm64" in the above command with the correct architecture. Possible values are "arm", "arm64", "x86", "x86_64". You can get the architecture of your phone with the command `adb shell getprop ro.product.cpu.abi`.

Copy frida-server to your phone, and run it:
```
DEST=/data/local/tmp
adb push frida-server-$VERSION-android-$ARCH $DEST
adb shell su -c "chmod 777 $DEST/frida-server-$VERSION-android-$ARCH"
adb shell su -c "$DEST/frida-server-$VERSION-android-$ARCH"
```

After running, do not close the terminal interface. Start a new terminal and enter:

```
adb forward tcp:27042 tcp:27042
adb forward tcp:27043 tcp:27043
frida-ps -U
```

If the terminal outputs some processes, it means that the environment has been set up successfully. Then, make sure your WeChat account is logged in on the phone, open WeChat, and run this command on your computer:

```
wget https://raw.githubusercontent.com/ellermister/wechat-clean/main/wechatdbpass.js
frida -U -n Wechat -l wechatdbpass.js
# 中文系统使用 frida -U -n 微信 -l wechatdbpass.js
```

The above command will print passwords for every database. Look for `EnMicroMsg.db` in the logs, e.g.:
```
SQLiteConnection: /data/user/0/com.tencent.mm/MicroMsg/XXXXXXXXXXXXXXXXXXXXXX/EnMicroMsg.db (0)
password: XXXXXX
```
