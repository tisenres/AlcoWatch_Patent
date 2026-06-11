package com.alcowatch.wearos.ble

import com.alcowatch.wearos.stress.StressLevel
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.UUID

object StressBLECharacteristic {

    val SERVICE_UUID: UUID = UUID.fromString("ABCD1234-1234-5678-1234-56789abcdef0")
    val CHARACTERISTIC_UUID: UUID = UUID.fromString("ABCD1235-1234-5678-1234-56789abcdef0")

    /**
     * Build 12-byte stress status packet:
     * [0-7]  timestamp ms (Long, little-endian)
     * [8]    stress level index (0-3)
     * [9]    confidence × 100, clamped to 0-100
     * [10-11] reserved (0x00)
     */
    fun buildPacket(
        level: StressLevel,
        confidence: Float,
        timestamp: Long = System.currentTimeMillis(),
    ): ByteArray {
        return ByteBuffer.allocate(12).order(ByteOrder.LITTLE_ENDIAN).apply {
            putLong(timestamp)
            put(level.index.toByte())
            put((confidence * 100).toInt().coerceIn(0, 100).toByte())
            put(0); put(0)
        }.array()
    }
}
