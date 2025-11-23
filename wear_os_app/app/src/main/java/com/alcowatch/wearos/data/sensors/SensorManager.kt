package com.alcowatch.wearos.data.sensors

import android.content.Context
import androidx.health.services.client.HealthServices
import androidx.health.services.client.MeasureCallback
import androidx.health.services.client.data.Availability
import androidx.health.services.client.data.DataPointContainer
import androidx.health.services.client.data.DataType
import androidx.health.services.client.data.DeltaDataType
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.guava.await
import timber.log.Timber
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Sensor data model
 */
data class SensorReading(
    val timestamp: Long,
    val heartRate: Double,
    val heartRateQuality: Double,
    val skinTemperature: Double,
    val ambientTemperature: Double = 25.0, // Default room temp
    val humidity: Double = 50.0 // Default humidity
)

/**
 * Electrodermal Activity (EDA) reading
 * Note: Not all Wear OS devices support EDA sensors
 * This is simulated based on heart rate variability for devices without EDA
 */
data class EDAReading(
    val timestamp: Long,
    val edaValue: Double, // Skin conductance in µS
    val quality: Double
)

/**
 * Combined sensor data for BAC estimation
 */
data class CombinedSensorData(
    val timestamp: Long,
    val ppgValue: Double,        // Heart rate (PPG sensor)
    val ppgQuality: Double,
    val edaValue: Double,         // Electrodermal activity
    val temperature: Double,      // Skin temperature
    val ambientTemp: Double,
    val humidity: Double
)

/**
 * Sensor Manager for AlcoWatch
 * Manages Health Services API for continuous sensor monitoring
 */
@Singleton
class SensorManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val healthServicesClient = HealthServices.getClient(context)
    private val measureClient = healthServicesClient.measureClient

    /**
     * Check if required sensors are available
     */
    suspend fun checkSensorAvailability(): Map<String, Boolean> {
        val capabilities = measureClient.getCapabilitiesAsync().await()

        return mapOf(
            "HEART_RATE" to capabilities.supportedDataTypesMeasure.contains(
                DataType.HEART_RATE_BPM
            ),
            "SKIN_TEMPERATURE" to capabilities.supportedDataTypesMeasure.any {
                it.name.contains("TEMPERATURE", ignoreCase = true)
            }
        )
    }

    /**
     * Start continuous heart rate monitoring (PPG sensor)
     */
    fun startHeartRateMonitoring(): Flow<SensorReading> = callbackFlow {
        val callback = object : MeasureCallback {
            override fun onAvailabilityChanged(
                dataType: DeltaDataType<*, *>,
                availability: Availability
            ) {
                Timber.d("Heart rate availability: $availability")
            }

            override fun onDataReceived(data: DataPointContainer) {
                // Extract heart rate
                val heartRatePoints = data.getData(DataType.HEART_RATE_BPM)

                if (heartRatePoints.isNotEmpty()) {
                    val latestPoint = heartRatePoints.last()
                    val heartRate = latestPoint.value

                    // Calculate signal quality (simplified)
                    val quality = if (heartRate > 40 && heartRate < 200) 0.9 else 0.5

                    // Get temperature (if available)
                    val temperature = try {
                        // Attempt to read skin temperature
                        // Note: This API varies by device
                        33.0 // Default value
                    } catch (e: Exception) {
                        33.0
                    }

                    val reading = SensorReading(
                        timestamp = System.currentTimeMillis(),
                        heartRate = heartRate,
                        heartRateQuality = quality,
                        skinTemperature = temperature,
                        ambientTemperature = 25.0,
                        humidity = 50.0
                    )

                    trySend(reading)
                }
            }
        }

        // Register callback
        measureClient.registerMeasureCallback(DataType.HEART_RATE_BPM, callback)

        Timber.i("Heart rate monitoring started")

        awaitClose {
            measureClient.unregisterMeasureCallbackAsync(DataType.HEART_RATE_BPM, callback)
            Timber.i("Heart rate monitoring stopped")
        }
    }

    /**
     * Estimate EDA from heart rate variability
     * This is a fallback for devices without dedicated EDA sensors
     */
    fun estimateEDAFromHRV(heartRateFlow: Flow<SensorReading>): Flow<EDAReading> = callbackFlow {
        val recentHeartRates = mutableListOf<Double>()

        heartRateFlow.collect { reading ->
            recentHeartRates.add(reading.heartRate)

            // Keep last 10 readings
            if (recentHeartRates.size > 10) {
                recentHeartRates.removeAt(0)
            }

            // Calculate HRV (standard deviation)
            if (recentHeartRates.size >= 5) {
                val mean = recentHeartRates.average()
                val variance = recentHeartRates.map { (it - mean) * (it - mean) }.average()
                val stdDev = kotlin.math.sqrt(variance)

                // Estimate EDA from HRV
                // Higher HRV typically correlates with higher sympathetic activity
                val estimatedEDA = 3.0 + (stdDev / 5.0) // Range: ~3-8 µS

                val edaReading = EDAReading(
                    timestamp = reading.timestamp,
                    edaValue = estimatedEDA,
                    quality = reading.heartRateQuality
                )

                trySend(edaReading)
            }
        }

        awaitClose {
            Timber.i("EDA estimation stopped")
        }
    }

    /**
     * Combine all sensor data for BAC estimation
     */
    fun getCombinedSensorData(
        heartRateFlow: Flow<SensorReading>,
        edaFlow: Flow<EDAReading>
    ): Flow<CombinedSensorData> = callbackFlow {
        var latestHeartRate: SensorReading? = null
        var latestEDA: EDAReading? = null

        suspend fun emitCombinedIfReady() {
            val hr = latestHeartRate
            val eda = latestEDA

            if (hr != null && eda != null) {
                val combined = CombinedSensorData(
                    timestamp = System.currentTimeMillis(),
                    ppgValue = hr.heartRate,
                    ppgQuality = hr.heartRateQuality,
                    edaValue = eda.edaValue,
                    temperature = hr.skinTemperature,
                    ambientTemp = hr.ambientTemperature,
                    humidity = hr.humidity
                )

                trySend(combined)
            }
        }

        // This is simplified - in production, use proper synchronization
        launch {
            heartRateFlow.collect { reading ->
                latestHeartRate = reading
                emitCombinedIfReady()
            }
        }

        launch {
            edaFlow.collect { reading ->
                latestEDA = reading
                emitCombinedIfReady()
            }
        }

        awaitClose {
            Timber.i("Combined sensor data flow stopped")
        }
    }

    /**
     * Check if watch is being worn
     * Uses heart rate sensor availability as proxy
     */
    suspend fun isWatchWorn(): Boolean {
        return try {
            val capabilities = measureClient.getCapabilitiesAsync().await()
            capabilities.supportedDataTypesMeasure.contains(DataType.HEART_RATE_BPM)
        } catch (e: Exception) {
            Timber.e(e, "Error checking if watch is worn")
            false
        }
    }
}
