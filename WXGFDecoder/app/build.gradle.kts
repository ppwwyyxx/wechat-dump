import com.android.build.api.dsl.Packaging

plugins {
    alias(libs.plugins.android.application)
}

android {
    namespace = "com.ppwwyyxx.wxgfdecoder"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.ppwwyyxx.wxgfdecoder"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("debug")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        viewBinding = true
    }
    packagingOptions {
        pickFirst( "jniLibs/arm64-v8a/libvoipCodec.so")
    }
}

dependencies {
    implementation("org.java-websocket:Java-WebSocket:1.5.4")
    implementation(libs.appcompat)
    implementation(libs.material)
    implementation(libs.constraintlayout)
    implementation(libs.lifecycle.livedata.ktx)
    implementation(libs.lifecycle.viewmodel.ktx)
    implementation(libs.navigation.fragment)
    implementation(libs.navigation.ui)
    testImplementation(libs.junit)
    androidTestImplementation(libs.ext.junit)
    androidTestImplementation(libs.espresso.core)
}
