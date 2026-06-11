package com.alcowatch.wearos.stress

import android.content.Context
import org.tensorflow.lite.Interpreter
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.channels.FileChannel

class StressInferenceEngine(private val context: Context) {

    private var interpreter: Interpreter? = null

    init { loadModel() }

    private fun loadModel() {
        val afd = context.assets.openFd("stress_model.tflite")
        val channel = afd.createInputStream().channel
        val buffer = channel.map(FileChannel.MapMode.READ_ONLY,
                                 afd.startOffset, afd.declaredLength)
        channel.close()
        afd.close()
        interpreter = Interpreter(buffer)
    }

    /**
     * Classify stress from a [30 x 5] sensor window.
     * Feature order: BVP, EDA, TEMP, ACC_magnitude, IBI
     * Returns (StressLevel, confidence 0..1)
     */
    fun classify(window: Array<FloatArray>): Pair<StressLevel, Float> {
        checkNotNull(interpreter) { "Stress model not loaded — cannot classify" }
        require(window.size == 30 && window[0].size == 5) {
            "Expected [30, 5], got [${window.size}, ${window[0].size}]"
        }
        val input = ByteBuffer.allocateDirect(30 * 5 * 4).order(ByteOrder.nativeOrder())
        for (step in window) for (f in step) input.putFloat(f)

        val output = Array(1) { FloatArray(4) }
        interpreter!!.run(input, output)

        val probs = output[0]
        val idx = probs.indices.maxByOrNull { probs[it] } ?: 0
        return StressLevel.fromIndex(idx) to probs[idx]
    }

    fun close() { interpreter?.close() }
}
