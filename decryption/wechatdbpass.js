// Source: https://github.com/ellermister/wechat-clean/blob/main/wechatdbpass.js
Java.performNow(function() {
    Java.choose("com.tencent.wcdb.database.SQLiteConnection", {
        onMatch: function(instance) {
            if(instance.mConnectionId.value != 0)return
            console.log(instance.toString());
            var buffer = instance.mPassword.value;
            if(buffer == null)buffer = []
            var result = "";
            for(var i = 0; i < buffer.length; ++i){
                result += (String.fromCharCode(buffer[i] & 0xff));
            }
            console.log(`password: ${result}`);
        }, onComplete: function() {
        }
    });
});
