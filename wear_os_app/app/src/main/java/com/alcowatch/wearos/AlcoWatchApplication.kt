package com.alcowatch.wearos

import android.app.Application
import dagger.hilt.android.HiltAndroidApp
import timber.log.Timber

/**
 * AlcoWatch Wear OS Application
 * Implements AI-based alcohol detection using smartwatch sensors
 */
@HiltAndroidApp
class AlcoWatchApplication : Application() {

    override fun onCreate() {
        super.onCreate()

        // Initialize Timber for logging
        if (BuildConfig.DEBUG) {
            Timber.plant(Timber.DebugTree())
        }

        Timber.i("AlcoWatch Application Started")
    }
}
