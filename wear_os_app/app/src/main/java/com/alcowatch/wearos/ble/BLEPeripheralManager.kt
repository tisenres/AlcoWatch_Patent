package com.alcowatch.wearos.ble

import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.AdvertiseCallback
import android.bluetooth.le.AdvertiseData
import android.bluetooth.le.AdvertiseSettings
import android.bluetooth.le.BluetoothLeAdvertiser
import android.content.Context
import android.os.ParcelUuid
import com.alcowatch.wearos.ml.AlertLevel
import com.alcowatch.wearos.ml.BACEstimate
import dagger.hilt.android.qualifiers.ApplicationContext
import timber.log.Timber
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * BLE UUIDs as defined in the protocol specification
 */
object BLEProtocol {
    val SERVICE_UUID: UUID = UUID.fromString("12345678-1234-5678-1234-56789abcdef0")
    val BAC_STATUS_UUID: UUID = UUID.fromString("12345678-1234-5678-1234-56789abcdef1")
    val VEHICLE_COMMAND_UUID: UUID = UUID.fromString("12345678-1234-5678-1234-56789abcdef2")
    val SYSTEM_STATUS_UUID: UUID = UUID.fromString("12345678-1234-5678-1234-56789abcdef3")
}

/**
 * Vehicle commands
 */
enum class VehicleCommand(val value: Byte) {
    ALLOW_IGNITION(0x00),
    BLOCK_IGNITION(0x01),
    REQUEST_VERIFICATION(0x02),
    OVERRIDE_REQUEST(0x03),
    EMERGENCY_OVERRIDE(0x04)
}

/**
 * BLE Peripheral Manager for AlcoWatch
 * Implements the smartwatch side of the BLE communication protocol
 */
@Singleton
class BLEPeripheralManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val bluetoothManager: BluetoothManager =
        context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager

    private val bluetoothAdapter: BluetoothAdapter? = bluetoothManager.adapter
    private var bluetoothGattServer: BluetoothGattServer? = null
    private var advertiser: BluetoothLeAdvertiser? = null

    // Connected devices
    private val connectedDevices = mutableSetOf<BluetoothDevice>()

    // Characteristics
    private var bacStatusCharacteristic: BluetoothGattCharacteristic? = null
    private var vehicleCommandCharacteristic: BluetoothGattCharacteristic? = null
    private var systemStatusCharacteristic: BluetoothGattCharacteristic? = null

    // Callback for vehicle commands
    var onVehicleCommandReceived: ((VehicleCommand, ByteArray) -> Unit)? = null

    /**
     * Start BLE advertising and GATT server
     */
    @SuppressLint("MissingPermission")
    fun startAdvertising() {
        if (bluetoothAdapter == null || !bluetoothAdapter.isEnabled) {
            Timber.e("Bluetooth not available or not enabled")
            return
        }

        advertiser = bluetoothAdapter.bluetoothLeAdvertiser

        if (advertiser == null) {
            Timber.e("BLE advertising not supported")
            return
        }

        // Setup GATT server
        setupGattServer()

        // Configure advertising
        val settings = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setConnectable(true)
            .setTimeout(0)
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            .build()

        val data = AdvertiseData.Builder()
            .setIncludeDeviceName(true)
            .addServiceUuid(ParcelUuid(BLEProtocol.SERVICE_UUID))
            .build()

        advertiser?.startAdvertising(settings, data, advertisingCallback)

        Timber.i("BLE advertising started")
    }

    /**
     * Setup GATT server with AlcoWatch service
     */
    @SuppressLint("MissingPermission")
    private fun setupGattServer() {
        bluetoothGattServer = bluetoothManager.openGattServer(context, gattServerCallback)

        // Create service
        val service = BluetoothGattService(
            BLEProtocol.SERVICE_UUID,
            BluetoothGattService.SERVICE_TYPE_PRIMARY
        )

        // BAC Status Characteristic (Read, Notify)
        bacStatusCharacteristic = BluetoothGattCharacteristic(
            BLEProtocol.BAC_STATUS_UUID,
            BluetoothGattCharacteristic.PROPERTY_READ or
                    BluetoothGattCharacteristic.PROPERTY_NOTIFY,
            BluetoothGattCharacteristic.PERMISSION_READ
        )

        // Add descriptor for notifications
        val bacDescriptor = BluetoothGattDescriptor(
            UUID.fromString("00002902-0000-1000-8000-00805f9b34fb"),
            BluetoothGattDescriptor.PERMISSION_READ or BluetoothGattDescriptor.PERMISSION_WRITE
        )
        bacStatusCharacteristic?.addDescriptor(bacDescriptor)

        // Vehicle Command Characteristic (Read, Write)
        vehicleCommandCharacteristic = BluetoothGattCharacteristic(
            BLEProtocol.VEHICLE_COMMAND_UUID,
            BluetoothGattCharacteristic.PROPERTY_READ or
                    BluetoothGattCharacteristic.PROPERTY_WRITE,
            BluetoothGattCharacteristic.PERMISSION_READ or
                    BluetoothGattCharacteristic.PERMISSION_WRITE
        )

        // System Status Characteristic (Read, Notify)
        systemStatusCharacteristic = BluetoothGattCharacteristic(
            BLEProtocol.SYSTEM_STATUS_UUID,
            BluetoothGattCharacteristic.PROPERTY_READ or
                    BluetoothGattCharacteristic.PROPERTY_NOTIFY,
            BluetoothGattCharacteristic.PERMISSION_READ
        )

        val systemDescriptor = BluetoothGattDescriptor(
            UUID.fromString("00002902-0000-1000-8000-00805f9b34fb"),
            BluetoothGattDescriptor.PERMISSION_READ or BluetoothGattDescriptor.PERMISSION_WRITE
        )
        systemStatusCharacteristic?.addDescriptor(systemDescriptor)

        // Add characteristics to service
        service.addCharacteristic(bacStatusCharacteristic)
        service.addCharacteristic(vehicleCommandCharacteristic)
        service.addCharacteristic(systemStatusCharacteristic)

        // Add service to GATT server
        bluetoothGattServer?.addService(service)

        Timber.i("GATT server configured")
    }

    /**
     * Send BAC update to connected vehicles
     */
    @SuppressLint("MissingPermission")
    fun sendBACUpdate(bacEstimate: BACEstimate, isWatchWorn: Boolean, batteryLevel: Float) {
        val data = encodeBACStatus(bacEstimate, isWatchWorn, batteryLevel)

        bacStatusCharacteristic?.value = data

        // Notify all connected devices
        connectedDevices.forEach { device ->
            try {
                bluetoothGattServer?.notifyCharacteristicChanged(
                    device,
                    bacStatusCharacteristic,
                    false
                )
                Timber.d("BAC update sent to ${device.address}")
            } catch (e: Exception) {
                Timber.e(e, "Failed to send BAC update")
            }
        }
    }

    /**
     * Encode BAC status according to protocol
     * Format (20 bytes):
     * Bytes 0-7: Timestamp (64-bit)
     * Bytes 8-11: BAC Value (float, 32-bit)
     * Byte 12: Alert Level
     * Byte 13: Confidence
     * Byte 14: Flags
     * Bytes 15-19: MAC (simplified)
     */
    private fun encodeBACStatus(
        bacEstimate: BACEstimate,
        isWatchWorn: Boolean,
        batteryLevel: Float
    ): ByteArray {
        val buffer = ByteBuffer.allocate(20)
        buffer.order(ByteOrder.LITTLE_ENDIAN)

        // Timestamp
        buffer.putLong(bacEstimate.timestamp)

        // BAC value
        buffer.putFloat(bacEstimate.bacValue)

        // Alert level
        val alertLevelByte = when (bacEstimate.alertLevel) {
            AlertLevel.SAFE -> 0x00.toByte()
            AlertLevel.WARNING -> 0x01.toByte()
            AlertLevel.DANGER -> 0x02.toByte()
            AlertLevel.CRITICAL -> 0x03.toByte()
        }
        buffer.put(alertLevelByte)

        // Confidence (0-100%)
        buffer.put((bacEstimate.confidence * 100).toInt().toByte())

        // Flags
        var flags = 0
        if (isWatchWorn) flags = flags or 0x01
        if (batteryLevel > 20) flags = flags or 0x04 // Sensor quality OK
        if (batteryLevel < 20) flags = flags or 0x08 // Battery low
        buffer.put(flags.toByte())

        // MAC (simplified - in production, use proper HMAC)
        val mac = ByteArray(5) { 0xFF.toByte() }
        buffer.put(mac)

        return buffer.array()
    }

    /**
     * Send system status update
     */
    @SuppressLint("MissingPermission")
    fun sendSystemStatus(
        batteryLevel: Float,
        isWatchWorn: Boolean,
        lastBACUpdate: Long
    ) {
        val data = encodeSystemStatus(batteryLevel, isWatchWorn, lastBACUpdate)

        systemStatusCharacteristic?.value = data

        connectedDevices.forEach { device ->
            try {
                bluetoothGattServer?.notifyCharacteristicChanged(
                    device,
                    systemStatusCharacteristic,
                    false
                )
            } catch (e: Exception) {
                Timber.e(e, "Failed to send system status")
            }
        }
    }

    /**
     * Encode system status (16 bytes)
     */
    private fun encodeSystemStatus(
        batteryLevel: Float,
        isWatchWorn: Boolean,
        lastBACUpdate: Long
    ): ByteArray {
        val buffer = ByteBuffer.allocate(16)
        buffer.order(ByteOrder.LITTLE_ENDIAN)

        // Device status
        buffer.put(0x00.toByte()) // Operational

        // Battery level
        buffer.putFloat(batteryLevel)

        // Last BAC update timestamp
        buffer.putInt((lastBACUpdate / 1000).toInt())

        // Connection quality (simplified)
        buffer.put(95.toByte())

        // Tamper status
        val tamperStatus = if (isWatchWorn) 0x00.toByte() else 0x01.toByte()
        buffer.put(tamperStatus)

        // Reserved
        buffer.put(ByteArray(5))

        return buffer.array()
    }

    /**
     * Stop advertising and close GATT server
     */
    @SuppressLint("MissingPermission")
    fun stopAdvertising() {
        advertiser?.stopAdvertising(advertisingCallback)
        bluetoothGattServer?.close()
        bluetoothGattServer = null
        connectedDevices.clear()

        Timber.i("BLE advertising stopped")
    }

    /**
     * Advertising callback
     */
    private val advertisingCallback = object : AdvertiseCallback() {
        override fun onStartSuccess(settingsInEffect: AdvertiseSettings) {
            Timber.i("BLE advertising started successfully")
        }

        override fun onStartFailure(errorCode: Int) {
            Timber.e("BLE advertising failed: $errorCode")
        }
    }

    /**
     * GATT server callback
     */
    private val gattServerCallback = object : BluetoothGattServerCallback() {
        @SuppressLint("MissingPermission")
        override fun onConnectionStateChange(device: BluetoothDevice, status: Int, newState: Int) {
            when (newState) {
                BluetoothProfile.STATE_CONNECTED -> {
                    connectedDevices.add(device)
                    Timber.i("Device connected: ${device.address}")
                }
                BluetoothProfile.STATE_DISCONNECTED -> {
                    connectedDevices.remove(device)
                    Timber.i("Device disconnected: ${device.address}")
                }
            }
        }

        @SuppressLint("MissingPermission")
        override fun onCharacteristicReadRequest(
            device: BluetoothDevice,
            requestId: Int,
            offset: Int,
            characteristic: BluetoothGattCharacteristic
        ) {
            bluetoothGattServer?.sendResponse(
                device,
                requestId,
                BluetoothGatt.GATT_SUCCESS,
                offset,
                characteristic.value
            )
        }

        @SuppressLint("MissingPermission")
        override fun onCharacteristicWriteRequest(
            device: BluetoothDevice,
            requestId: Int,
            characteristic: BluetoothGattCharacteristic,
            preparedWrite: Boolean,
            responseNeeded: Boolean,
            offset: Int,
            value: ByteArray
        ) {
            if (characteristic.uuid == BLEProtocol.VEHICLE_COMMAND_UUID) {
                handleVehicleCommand(value)
            }

            if (responseNeeded) {
                bluetoothGattServer?.sendResponse(
                    device,
                    requestId,
                    BluetoothGatt.GATT_SUCCESS,
                    offset,
                    value
                )
            }
        }
    }

    /**
     * Handle incoming vehicle command
     */
    private fun handleVehicleCommand(data: ByteArray) {
        if (data.isEmpty()) return

        val commandByte = data[0]
        val command = when (commandByte) {
            0x00.toByte() -> VehicleCommand.ALLOW_IGNITION
            0x01.toByte() -> VehicleCommand.BLOCK_IGNITION
            0x02.toByte() -> VehicleCommand.REQUEST_VERIFICATION
            0x03.toByte() -> VehicleCommand.OVERRIDE_REQUEST
            0x04.toByte() -> VehicleCommand.EMERGENCY_OVERRIDE
            else -> {
                Timber.w("Unknown vehicle command: $commandByte")
                return
            }
        }

        Timber.i("Vehicle command received: $command")
        onVehicleCommandReceived?.invoke(command, data)
    }

    /**
     * Check if any vehicles are connected
     */
    fun isConnected(): Boolean = connectedDevices.isNotEmpty()

    /**
     * Get number of connected devices
     */
    fun getConnectedDeviceCount(): Int = connectedDevices.size
}
