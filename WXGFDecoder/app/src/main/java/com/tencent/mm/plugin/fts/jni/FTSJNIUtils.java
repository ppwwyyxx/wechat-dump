package com.tencent.mm.plugin.fts.jni;

public class FTSJNIUtils {
    public static native int countTokens(String str);

    public static native int icuInitialize(String str);

    public static native String icuTokenizer(String str);

    public static native void nativeInitFts(long j, byte[] bArr);

    public static native int stringCompareUtfBinary(String str, String str2);

}
