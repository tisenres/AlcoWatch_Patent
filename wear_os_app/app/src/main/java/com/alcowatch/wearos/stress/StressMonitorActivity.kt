package com.alcowatch.wearos.stress

import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattServer
import android.bluetooth.BluetoothGattService
import android.bluetooth.BluetoothManager
import android.content.Context
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.TextView
import androidx.activity.ComponentActivity
import com.alcowatch.wearos.ble.StressBLECharacteristic
import kotlin.math.sqrt

/**
 * Displays real-time stress level and broadcasts it via BLE every 30 s.
 *
 * Feature layout:
 *   window[step][0] = BVP, [1] = EDA, [2] = TEMP, [3] = ACC_magnitude, [4] = IBI
 *
 * In a production build, sensor data would be collected from SensorManager.
 * This activity wires the inference engine to the BLE characteristic and
 * provides a minimal UI showing the current stress level with color feedback.
 */
class StressMonitorActivity : ComponentActivity() {

    private lateinit var engine: StressInferenceEngine
    private lateinit var statusText: TextView
    private val handler = Handler(Looper.getMainLooper())

    private var gattServer: BluetoothGattServer? = null
    private var stressCharacteristic: BluetoothGattCharacteristic? = null

    companion object {
        private const val BROADCAST_INTERVAL_MS = 30_000L
        private const val WINDOW_SIZE = 30
        private const val N_FEATURES = 5
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        engine = StressInferenceEngine(applicationContext)

        statusText = TextView(this).apply {
            textSize = 18f
            text = "Initialising…"
        }
        setContentView(statusText)

        setupGattServer()
        handler.post(broadcastRunnable)
    }

    private val broadcastRunnable = object : Runnable {
        override fun run() {
            runInference()
            handler.postDelayed(this, BROADCAST_INTERVAL_MS)
        }
    }

    private fun runInference() {
        val window = buildDummyWindow()
        val (level, confidence) = engine.classify(window)
        updateUI(level, confidence)
        broadcastBle(level, confidence)
    }

    /**
     * Builds a [WINDOW_SIZE × N_FEATURES] window.
     * Replace with real SensorManager data in production.
     */
    private fun buildDummyWindow(): Array<FloatArray> =
        Array(WINDOW_SIZE) { FloatArray(N_FEATURES) }

    private fun updateUI(level: StressLevel, confidence: Float) {
        val color = when (level) {
            StressLevel.CALM     -> android.graphics.Color.WHITE
            StressLevel.MILD     -> android.graphics.Color.YELLOW
            StressLevel.MODERATE -> android.graphics.Color.rgb(255, 140, 0)
            StressLevel.CRITICAL -> android.graphics.Color.RED
        }
        statusText.text = "${level.displayName}\n${(confidence * 100).toInt()}% confidence"
        statusText.setTextColor(color)
    }

    private fun broadcastBle(level: StressLevel, confidence: Float) {
        val packet = StressBLECharacteristic.buildPacket(level, confidence)
        stressCharacteristic?.let { char ->
            char.value = packet
            gattServer?.notifyCharacteristicChanged(null, char, false)
        }
    }

    private fun setupGattServer() {
        val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        val adapter = bluetoothManager.adapter ?: return

        val service = BluetoothGattService(
            StressBLECharacteristic.SERVICE_UUID,
            BluetoothGattService.SERVICE_TYPE_PRIMARY,
        )
        val characteristic = BluetoothGattCharacteristic(
            StressBLECharacteristic.CHARACTERISTIC_UUID,
            BluetoothGattCharacteristic.PROPERTY_READ or BluetoothGattCharacteristic.PROPERTY_NOTIFY,
            BluetoothGattCharacteristic.PERMISSION_READ,
        )
        service.addCharacteristic(characteristic)
        stressCharacteristic = characteristic

        gattServer = bluetoothManager.openGattServer(this, object :
            android.bluetooth.BluetoothGattServerCallback() {
            override fun onConnectionStateChange(
                device: android.bluetooth.BluetoothDevice?,
                status: Int, newState: Int,
            ) {
                // Connection tracking handled by BLEPeripheralManager if integrated
            }
        })
        gattServer?.addService(service)
    }

    override fun onDestroy() {
        handler.removeCallbacks(broadcastRunnable)
        gattServer?.close()
        engine.close()
        super.onDestroy()
    }
}
