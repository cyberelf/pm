package net.cyberelf.reports.voice

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import java.io.ByteArrayOutputStream
import java.io.IOException
import kotlin.math.abs

/** Recording surface consumed by the ViewModel; lets tests substitute a
 *  fake recorder instead of touching AudioRecord on the JVM. */
interface VoiceRecorder {
    val isRecording: Boolean
    val recordedBytes: Int
    fun start()
    fun stop(): ByteArray
}

/** Captures mono 16 kHz 16-bit PCM with AudioRecord and produces a complete
 *  WAV file's bytes on stop. Runs the capture loop on a dedicated thread and
 *  reports peak amplitude (0..100) roughly 30x per second for UI metering.
 *
 *  MediaRecorder is deliberately not used: it cannot emit wav/mp3/flac, which
 *  are the only formats the ASR service accepts. */
class WavRecorder(
    private val sampleRate: Int = 16_000,
    private val onAmplitude: (Int) -> Unit = {},
) : VoiceRecorder {

    private var audioRecord: AudioRecord? = null
    private var captureThread: Thread? = null
    private val pcmBuffer = ByteArrayOutputStream()

    @Volatile
    private var capturing = false

    override val isRecording: Boolean get() = capturing

    override val recordedBytes: Int
        get() = synchronized(pcmBuffer) { pcmBuffer.size() }

    @SuppressLint("MissingPermission") // the record screen gates on the runtime grant
    override fun start() {
        check(!capturing) { "recorder already running" }
        val minBuffer = AudioRecord.getMinBufferSize(
            sampleRate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
        )
        if (minBuffer <= 0) throw IOException("麦克风不可用")
        val record = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            sampleRate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            maxOf(minBuffer, sampleRate), // 0.5s floor at 16 kHz mono 16-bit
        )
        if (record.state != AudioRecord.STATE_INITIALIZED) {
            record.release()
            throw IOException("麦克风初始化失败")
        }
        audioRecord = record
        synchronized(pcmBuffer) { pcmBuffer.reset() }
        capturing = true
        captureThread = Thread {
            val chunk = ShortArray(1024) // ~32 ms per read
            try {
                record.startRecording()
                while (capturing) {
                    val read = record.read(chunk, 0, chunk.size)
                    if (read <= 0) continue
                    var peak = 0
                    for (i in 0 until read) {
                        val magnitude = abs(chunk[i].toInt())
                        if (magnitude > peak) peak = magnitude
                    }
                    onAmplitude(peak * 100 / 32_768)
                    val bytes = ByteArray(read * 2)
                    for (i in 0 until read) {
                        val sample = chunk[i].toInt()
                        bytes[i * 2] = (sample and 0xff).toByte()
                        bytes[i * 2 + 1] = (sample shr 8 and 0xff).toByte()
                    }
                    synchronized(pcmBuffer) { pcmBuffer.write(bytes) }
                }
            } finally {
                runCatching { record.stop() }
                record.release()
            }
        }.also { it.start() }
    }

    /** Stops capture and returns the full WAV bytes recorded so far. */
    override fun stop(): ByteArray {
        if (!capturing) throw IOException("recorder is not running")
        capturing = false
        captureThread?.join(2_000)
        captureThread = null
        audioRecord = null
        val pcm = synchronized(pcmBuffer) { pcmBuffer.toByteArray() }
        return Wav.encodePcmToWav(pcm, sampleRate)
    }
}
