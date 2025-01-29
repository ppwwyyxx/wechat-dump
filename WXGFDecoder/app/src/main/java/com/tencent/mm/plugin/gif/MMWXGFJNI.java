//File:
package com.tencent.mm.plugin.gif;

import android.graphics.Bitmap;

import java.io.File;
/*
 *import com.tencent.matrix.trace.core.AppMethodBeat;
 *import com.tencent.mm.loader.p558j.C11743b;
 *import com.tencent.mm.sdk.platformtools.C52656ad;
 */

/* renamed from: com.tencent.mm.plugin.gif.MMWXGFJNI */
public class MMWXGFJNI {
    public static final int PIC_TYPE_JPG = 0;
    public static final int PIC_TYPE_PNG = 1;
    private static final String TAG = "MicroMsg.JNI.MMWXGF";
    static int mECode;
    public static boolean mIsInit;


    public static native int nativeAV2Gif(String str, String str2);

    public static native int nativeAV2Gif(byte[] bArr, byte[] bArr2);

    public static native int nativeAddGifEncodeRgbaFrame(long j, int i, int i2, byte[] bArr, long j2);

    public static native int nativeAddWxAMEncodeRgbaFrame(long j, int i, int i2, byte[] bArr, long j2);

    public static native int nativeDecodeBufferFrame(long j, byte[] bArr, int i, Bitmap bitmap, int[] iArr);

    public static native int nativeDecodeBufferHeader(long j, byte[] bArr, int i);

    public static native byte[] nativeFinishGifEncode(long j);

    public static native byte[] nativeFinishWxAMEncode(long j);

    public static native int nativeGetOption(long j, byte[] bArr, int i, int[] iArr);

    public static native int nativeInit(String str);

    public static native long nativeInitGifEncode(int i, int i2, long j);

    public static native long nativeInitWxAMDecoder();

    public static native long nativeInitWxAMEncoder(int i, int i2, long j, int i3);

    public static native boolean nativeIsWXGF(byte[] bArr, int i);

    public static native int nativePic2Wxam(String str, String str2, int i, int i2);

    public static native int nativePic2WxamWithWH(String str, String str2, int i, int i2, int i3, int i4);

    public static native int nativePic2WxamWithWH(String str, byte[] bArr, int i, int i2, int i3, int i4, int i5, int i6, int i7);

    public static native int nativeRewindBuffer(long j);

    public static native int nativeUninit(long j);

    public static native int nativeWxam2Pic(String str, String str2);

    public static native byte[] nativeWxam2PicBuf(byte[] bArr);

    public static native byte[] nativeWxamToGif(byte[] bArr);

    public static void initialize(String nativeDir) {
        // init wxgf decoder
        String soFilePath = nativeDir + "/libvoipCodec.so";
        File soFile = new File(soFilePath);
        if (!soFile.exists())
            throw new RuntimeException("missing so file " + soFilePath);
        int initSuccess = nativeInit(soFilePath); // return -1 if missing so
        if (initSuccess < 0)
            throw new RuntimeException("nativeInit failed " + initSuccess);
        mIsInit = true;
    }
    /* // Original code below:
     *static {
     *    AppMethodBeat.m13231i(104681);
     *    mIsInit = false;
     *    mECode = -1;
     *    C52656ad.m88211i(TAG, "static MMWXGFJNI");
     *    if (!mIsInit) {
     *        String str = C11743b.ahY() + "lib/libvoipCodec.so";
     *        int nativeInit = nativeInit(str);
     *        mECode = nativeInit;
     *        mIsInit = nativeInit >= 0;
     *        C52656ad.m88212i(TAG, "native init MMWXGF mECode:%d result:%b :%s", Integer.valueOf(mECode), Boolean.valueOf(mIsInit), str);
     *        AppMethodBeat.m13232o(104681);
     *        return;
     *    }
     *    C52656ad.m88205d(TAG, "MMWXGF has init.");
     *    AppMethodBeat.m13232o(104681);
     *}
     */

    public static int getErrorCode() {
        return mECode;
    }
}

