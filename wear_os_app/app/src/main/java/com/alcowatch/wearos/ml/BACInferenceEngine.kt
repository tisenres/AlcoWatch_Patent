package com.alcowatch.wearos.ml

import android.content.Context
import com.alcowatch.wearos.data.sensors.CombinedSensorData
import dagger.hilt.android.qualifiers.ApplicationContext
import org.tensorflow.lite.Interpreter
import timber.log.Timber
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel
import javax.inject.Inject
import javax.inject.Singleton

/**
 * BAC estimation result
 */
data class BACEstimate(
    val bacValue: Float,       // BAC in g/dL
    val confidence: Float,      // Confidence score 0-1
    val alertLevel: AlertLevel,
    val timestamp: Long
)

/**
 * Alert levels based on BAC
 */
enum class AlertLevel {
    SAFE,      // BAC < 0.05
    WARNING,   // BAC 0.05-0.08
    DANGER,    // BAC 0.08-0.15
    CRITICAL   // BAC > 0.15
}

/**
 * Climate calibration parameters
 */
data class ClimateCalibration(
    val region: String = "Default",
    val tempCoefficient: Float = 0.011f,
    val humidityCoefficient: Float = 0.007f,
    val baseTemp: Float = 25.0f
)

/**
 * TensorFlow Lite inference engine for BAC estimation
 * Implements the patent's AI-based sensor fusion algorithm
 */
@Singleton
class BACInferenceEngine @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private var interpreter: Interpreter? = null
    private val sequenceLength = 10
    private val numFeatures = 6

    // Circular buffer for sensor readings
    private val sensorBuffer = mutableListOf<FloatArray>()

    // Climate calibration
    private var calibration = ClimateCalibration()

    // Feature normalization parameters (from training)
    private val featureMeans = floatArrayOf(
        80.0f,   // ppg_heart_rate
        0.9f,    // ppg_quality
        5.0f,    // eda_value
        33.0f,   // temperature
        25.0f,   // ambient_temp
        50.0f    // humidity
    )

    private val featureStdDevs = floatArrayOf(
        15.0f,   // ppg_heart_rate
        0.1f,    // ppg_quality
        2.0f,    // eda_value
        1.5f,    // temperature
        5.0f,    // ambient_temp
        15.0f    // humidity
    )

    /**
     * Initialize TensorFlow Lite model
     */
    fun initialize(modelPath: String = "bac_model.tflite") {
        try {
            val modelBuffer = loadModelFile(modelPath)
            interpreter = Interpreter(modelBuffer)
            Timber.i("TFLite model loaded successfully")
        } catch (e: Exception) {
            Timber.e(e, "Failed to load TFLite model")
        }
    }

    /**
     * Load TFLite model from assets
     */
    private fun loadModelFile(modelPath: String): MappedByteBuffer {
        val fileDescriptor = context.assets.openFd(modelPath)
        val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
        val fileChannel = inputStream.channel
        val startOffset = fileDescriptor.startOffset
        val declaredLength = fileDescriptor.declaredLength
        return fileChannel.map(FileChannel.MapMode.READ_ONLY, startOffset, declaredLength)
    }

    /**
     * Set climate calibration parameters
     */
    fun setClimateCalibration(calibration: ClimateCalibration) {
        this.calibration = calibration
        Timber.d("Climate calibration set: ${calibration.region}")
    }

    /**
     * Process new sensor reading and estimate BAC
     */
    fun processSensorData(sensorData: CombinedSensorData): BACEstimate? {
        // Convert sensor data to feature array
        val features = floatArrayOf(
            sensorData.ppgValue.toFloat(),
            sensorData.ppgQuality.toFloat(),
            sensorData.edaValue.toFloat(),
            sensorData.temperature.toFloat(),
            sensorData.ambientTemp.toFloat(),
            sensorData.humidity.toFloat()
        )

        // Normalize features
        val normalizedFeatures = normalizeFeatures(features)

        // Add to buffer
        sensorBuffer.add(normalizedFeatures)

        // Keep only last sequenceLength readings
        if (sensorBuffer.size > sequenceLength) {
            sensorBuffer.removeAt(0)
        }

        // Need full sequence for prediction
        if (sensorBuffer.size < sequenceLength) {
            Timber.d("Collecting sensor data: ${sensorBuffer.size}/$sequenceLength")
            return null
        }

        // Run inference
        return runInference(sensorData.timestamp, sensorData.ambientTemp, sensorData.humidity)
    }

    /**
     * Normalize sensor features
     */
    private fun normalizeFeatures(features: FloatArray): FloatArray {
        return FloatArray(features.size) { i ->
            (features[i] - featureMeans[i]) / featureStdDevs[i]
        }
    }

    /**
     * Run TensorFlow Lite inference
     */
    private fun runInference(
        timestamp: Long,
        ambientTemp: Double,
        humidity: Double
    ): BACEstimate? {
        val interp = interpreter ?: run {
            Timber.w("Interpreter not initialized")
            return null
        }

        try {
            // Prepare input tensor [1, sequence_length, num_features]
            val inputBuffer = ByteBuffer.allocateDirect(4 * sequenceLength * numFeatures)
            inputBuffer.order(ByteOrder.nativeOrder())

            for (features in sensorBuffer) {
                for (feature in features) {
                    inputBuffer.putFloat(feature)
                }
            }

            // Prepare output tensor [1, 1]
            val outputBuffer = ByteBuffer.allocateDirect(4)
            outputBuffer.order(ByteOrder.nativeOrder())

            // Run inference
            interp.run(inputBuffer, outputBuffer)

            // Extract BAC prediction
            outputBuffer.rewind()
            val rawBac = outputBuffer.float

            // Apply climate calibration
            val calibratedBac = applyClimateCalibration(
                rawBac,
                ambientTemp.toFloat(),
                humidity.toFloat()
            )

            // Ensure non-negative
            val finalBac = maxOf(0f, calibratedBac)

            // Calculate confidence (simplified)
            val confidence = calculateConfidence(finalBac)

            // Determine alert level
            val alertLevel = determineAlertLevel(finalBac)

            Timber.d("BAC Estimate: $finalBac g/dL (Alert: $alertLevel)")

            return BACEstimate(
                bacValue = finalBac,
                confidence = confidence,
                alertLevel = alertLevel,
                timestamp = timestamp
            )

        } catch (e: Exception) {
            Timber.e(e, "Inference error")
            return null
        }
    }

    /**
     * Apply climate-specific calibration
     * Implements patent's climate-adaptive feature
     */
    private fun applyClimateCalibration(
        rawBac: Float,
        ambientTemp: Float,
        humidity: Float
    ): Float {
        // Temperature adjustment
        val tempDiff = ambientTemp - calibration.baseTemp
        val tempAdjustment = tempDiff * calibration.tempCoefficient

        // Humidity adjustment
        val humidityAdjustment = (humidity - 50f) * calibration.humidityCoefficient / 100f

        return rawBac + tempAdjustment + humidityAdjustment
    }

    /**
     * Calculate confidence score
     */
    private fun calculateConfidence(bacValue: Float): Float {
        // Simplified confidence calculation
        // In practice, this would use ensemble uncertainty or MC dropout
        return when {
            bacValue < 0.02 -> 0.95f  // Very confident when sober
            bacValue < 0.1 -> 0.90f   // High confidence in typical range
            bacValue < 0.2 -> 0.85f   // Moderate confidence
            else -> 0.75f              // Lower confidence at extreme values
        }
    }

    /**
     * Determine alert level from BAC value
     */
    private fun determineAlertLevel(bacValue: Float): AlertLevel {
        return when {
            bacValue < 0.05f -> AlertLevel.SAFE
            bacValue < 0.08f -> AlertLevel.WARNING
            bacValue < 0.15f -> AlertLevel.DANGER
            else -> AlertLevel.CRITICAL
        }
    }

    /**
     * Check if BAC exceeds legal limit
     */
    fun isOverLegalLimit(bacEstimate: BACEstimate, legalLimit: Float = 0.08f): Boolean {
        return bacEstimate.bacValue > legalLimit
    }

    /**
     * Reset sensor buffer (e.g., when watch is removed/worn again)
     */
    fun resetBuffer() {
        sensorBuffer.clear()
        Timber.d("Sensor buffer reset")
    }

    /**
     * Clean up resources
     */
    fun close() {
        interpreter?.close()
        interpreter = null
        Timber.i("Inference engine closed")
    }

    /**
     * Get current buffer status
     */
    fun getBufferStatus(): Pair<Int, Int> {
        return Pair(sensorBuffer.size, sequenceLength)
    }
}
