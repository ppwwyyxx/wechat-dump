You can also obtain the access password through Frida. If you have a python environment on your computer, it is recommended to use this method, because this method can directly obtain the password without having to try the spliced ​​passwords one by one, and it is absolutely correct. First, install the Frida package on your computer using the following command:

```
pip install frida
pip install frida-tools
```

Then use adb to view the mobile phone architecture:

```
adb shell getprop ro.product.cpu.abi
```

What you get is arm64-v8a, then go to https://github.com/frida/frida/releases page to download the corresponding frida-server--arm64.xz package, and then unzip it. Note: The version number of frida-server here must be consistent with the version number of frrida installed on the computer above, otherwise additional errors may occur. Transfer frida-server to the phone through adb:

```
adb push frida-server-<version>-android-arm /data/local/tmp
```

Then run frida-server on your phone:

```
adb shell
su
cd /data/local/tmp
chmod 777 frida-server-<version>-android-arm
./frida-server-<version>-android-arm
```

After running, do not close the terminal interface. In addition, start a terminal and enter:

```
adb forward tcp:27042 tcp:27042
adb forward tcp:27043 tcp:27043
frida-ps -U
```

If the terminal outputs some processes, it means that the environment has been set up successfully. After the setup is successful, run the following Python script on your computer:

```
wget https://raw.githubusercontent.com/ellermister/wechat-clean/main/wechatdbpass.js
frida -U -n Wechat -l wechatdbpass.js
```

(guide translated from https://blog.greycode.top/posts/android-wechat-bak/ and https://github.com/ellermister/wechat-clean/blob/main/wechatdbpass.js )
