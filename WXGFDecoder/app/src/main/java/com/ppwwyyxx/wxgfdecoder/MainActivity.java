package com.ppwwyyxx.wxgfdecoder;

import android.content.Context;
import android.os.Build;
import android.os.PowerManager;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.EditText;

import com.tencent.mm.plugin.gif.MMWXGFJNI;

import androidx.appcompat.app.AppCompatActivity;

import com.ppwwyyxx.wxgfdecoder.databinding.ActivityMainBinding;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.util.Arrays;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.util.Collections;
import java.util.List;


import org.java_websocket.WebSocket;
import org.java_websocket.handshake.ClientHandshake;
import org.java_websocket.server.WebSocketServer;

public class MainActivity extends AppCompatActivity {

    private ActivityMainBinding binding;
    private Button startButton;
    private TextView hostnameTextView, portTextView, logTextView;
    private EditText portEditText;
    private WebSocketServer server;

    static {
        System.loadLibrary("wechatcommon");
    }


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        // Keep screen on
        getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        // If the app is running on Android 8.0 or higher, request for ignoring battery optimizations
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            PowerManager powerManager = (PowerManager) getSystemService(Context.POWER_SERVICE);
            if (!powerManager.isIgnoringBatteryOptimizations(getPackageName())) {
                // TODO: request for ignoring battery optimizations
            }
        }

        MMWXGFJNI.initialize(getApplicationInfo().nativeLibraryDir);

        // Set up UI
        startButton = findViewById(R.id.start_server_button);
        hostnameTextView = findViewById(R.id.text_view_hostname);
        portTextView = findViewById(R.id.text_view_port);
        portEditText = findViewById(R.id.edit_text_port);
        logTextView = findViewById(R.id.log_text_area);
        logTextView.setText("");
        startButton.setOnClickListener(v -> {
            try {
                startWebSocketServer();
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        });

        // Run a unit test:
        testWxgfDecoder();
    }

    private void startWebSocketServer() throws InterruptedException {
        if (server != null) {
            server.stop();
            server = null;
        }

        int port;
        try {
            port = Integer.parseInt(portEditText.getText().toString());
        } catch (NumberFormatException e) {
            port = 8080;
        }
        try {
            server = new WebSocketServer(new InetSocketAddress(port)) {
                @Override
                public void onOpen(WebSocket conn, ClientHandshake handshake) {
                    printLog("new connection from " + conn.getRemoteSocketAddress().getAddress().getHostAddress());
                }

                @Override
                public void onClose(WebSocket conn, int code, String reason, boolean remote) {
                    printLog("closed " + conn.getRemoteSocketAddress() + " with exit code " + code + " additional info: " + reason);
                }
                @Override
                public void onMessage( WebSocket conn, ByteBuffer message ) {
                    byte[] msg = message.array();

                    printLog("received binary message from " + conn.getRemoteSocketAddress() + ": size=" + msg.length
                            + " -- " + Arrays.toString(Arrays.copyOfRange(msg, 0, 10)));

                    byte[] res = com.tencent.mm.plugin.gif.MMWXGFJNI.nativeWxam2PicBuf(msg);
                    if (res != null) {
                        printLog("After decoding: size=" + res.length + " -- " +
                                Arrays.toString(Arrays.copyOfRange(res, 0, 10)));
                        ByteBuffer response = ByteBuffer.wrap(res);
                        conn.send(response); // the response gif
                    } else {
                        printLog("Failed to decode.");
                        conn.send("FAILED".getBytes());
                    }
                }

                @Override
                public void onMessage( WebSocket conn, String message) {
                    printLog("Unexpected! received text message from " + conn.getRemoteSocketAddress() + ": " + message);
                }

                @Override
                public void onError(WebSocket conn, Exception ex) {
                    printLog("an error occurred on connection " + conn + ":" + ex);
                }

                @Override
                public void onStart() {
                    try {
                        String hostName = getLocalIpAddress(true);
                        int port = server.getPort();
                        printLog("server started successfully at ws://" + hostName + ":" + port);

                        runOnUiThread(() -> { // update UI in UI thread
                            hostnameTextView.setText("Hostname: " + hostName);
                            portTextView.setText("Port: " + String.valueOf(port));
                        });
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }
            };
            server.start();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void printLog(String log) {
        System.out.println(log);
        runOnUiThread(() -> {
            String currentLog = logTextView.getText().toString();
            logTextView.setText(currentLog + "\n" + log);
        });
    }

    public String getLocalIpAddress(boolean useIPv4) throws SocketException {
        List<NetworkInterface> interfaces = Collections.list(NetworkInterface.getNetworkInterfaces());
        for (NetworkInterface intf : interfaces) {
            List<InetAddress> addrs = Collections.list(intf.getInetAddresses());
            for (InetAddress addr : addrs) {
                if (!addr.isLoopbackAddress()) {
                    String sAddr = addr.getHostAddress();
                    boolean isIPv4 = sAddr.indexOf(':')<0;
                    if (useIPv4) {
                        if (isIPv4)
                            return sAddr;
                    } else {
                        return sAddr;
                    }
                }
            }        }
        return "localhost";
    }

    // Methods below are for debugging the decoder:
    private void testWxgfDecoder() {
        byte[] wxgf = null;
        try {
            wxgf = readBinary(this);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        System.out.println("Unit test: wxgf size=" + wxgf.length);
        byte[] res = com.tencent.mm.plugin.gif.MMWXGFJNI.nativeWxam2PicBuf(wxgf);
        System.out.println("Unit test: res size=" + res.length + " -- " + Arrays.toString(Arrays.copyOfRange(res, 0, 10)));

        try {
            writeFile(this, "test.jpg", res);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        if (wxgf.length != 64367 || res.length != 705188) {
            throw new RuntimeException("test failed");
        }
    }
    public static byte[] readBinary(Context context) throws IOException {
        InputStream inputStream = context.getResources().openRawResource(R.raw.test_wxgf); // R.raw.image refers to your image.jpg file
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        byte[] buffer = new byte[1024];
        int len;
        while ((len = inputStream.read(buffer)) != -1) {
            byteArrayOutputStream.write(buffer, 0, len);
        }
        inputStream.close(); // Close the input stream
        return byteArrayOutputStream.toByteArray();
    }

    public static void writeFile(Context context, String filename, byte[] data) throws IOException {
        File file = new File(context.getExternalFilesDir(null), filename); // Use null for the type argument to get the root external files directory
        System.out.println("Writing file to: " + file.getAbsolutePath());
        FileOutputStream outputStream = new FileOutputStream(file);
        outputStream.write(data);
        outputStream.close();
    }
}
