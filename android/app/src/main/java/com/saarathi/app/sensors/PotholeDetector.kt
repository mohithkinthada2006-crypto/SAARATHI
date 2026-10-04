package com.saarathi.app.sensors

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import kotlin.math.sqrt

/**
 * On-device Pothole & Road Hazard Detector.
 * Leverages phone accelerometer at high sampling rate with a high-pass gravity filter
 * to isolate sharp vertical and linear shock impulses on road surfaces.
 */
class PotholeDetector(
    context: Context,
    private val onPothole: (magnitude: Float) -> Unit
) : SensorEventListener {

    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as? SensorManager
    private val accelerometer: Sensor? = sensorManager?.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)

    private val gravity = FloatArray(3) { 0f }
    private val alpha = 0.8f
    private val threshold = 15.0f // Acceleration shock threshold in m/s^2
    private val minGapMs = 500L    // Minimum cooldown interval between distinct pothole events
    private var lastSpikeTimestampMs = 0L

    fun start() {
        accelerometer?.let {
            sensorManager?.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
        }
    }

    fun stop() {
        sensorManager?.unregisterListener(this)
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event == null || event.sensor.type != Sensor.TYPE_ACCELEROMETER) return

        // High-pass filter isolating dynamic linear acceleration from earth gravity
        gravity[0] = alpha * gravity[0] + (1 - alpha) * event.values[0]
        gravity[1] = alpha * gravity[1] + (1 - alpha) * event.values[1]
        gravity[2] = alpha * gravity[2] + (1 - alpha) * event.values[2]

        val linearX = event.values[0] - gravity[0]
        val linearY = event.values[1] - gravity[1]
        val linearZ = event.values[2] - gravity[2]

        val magnitude = sqrt(linearX * linearX + linearY * linearY + linearZ * linearZ)
        val currentMs = System.currentTimeMillis()

        if (magnitude >= threshold && (currentMs - lastSpikeTimestampMs) >= minGapMs) {
            lastSpikeTimestampMs = currentMs
            onPothole(magnitude)
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        // No-op
    }
}
