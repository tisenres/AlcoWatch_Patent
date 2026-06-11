package com.alcowatch.wearos.stress

enum class StressLevel(val index: Int, val displayName: String) {
    CALM(0, "Calm"),
    MILD(1, "Mild Stress"),
    MODERATE(2, "Moderate Stress"),
    CRITICAL(3, "Critical Stress");

    companion object {
        fun fromIndex(index: Int): StressLevel =
            entries.firstOrNull { it.index == index } ?: CALM
    }
}
