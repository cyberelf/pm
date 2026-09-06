package net.cyberelf.reports.voice

/** Pure WAV (RIFF) container writing for the PCM frames captured by
 *  [WavRecorder]. The ASR service only accepts wav/mp3/flac, so recordings
 *  are wrapped here before upload. */
object Wav {

    fun encodePcmToWav(
        pcm: ByteArray,
        sampleRate: Int = 16_000,
        channels: Int = 1,
        bitsPerSample: Int = 16,
    ): ByteArray {
        val out = ByteArray(44 + pcm.size)
        writeAscii(out, 0, "RIFF")
        writeIntLe(out, 4, 36 + pcm.size)
        writeAscii(out, 8, "WAVE")
        writeAscii(out, 12, "fmt ")
        writeIntLe(out, 16, 16) // PCM chunk size
        writeShortLe(out, 20, 1) // format tag: PCM
        writeShortLe(out, 22, channels)
        writeIntLe(out, 24, sampleRate)
        writeIntLe(out, 28, sampleRate * channels * bitsPerSample / 8) // byte rate
        writeShortLe(out, 32, channels * bitsPerSample / 8) // block align
        writeShortLe(out, 34, bitsPerSample)
        writeAscii(out, 36, "data")
        writeIntLe(out, 40, pcm.size)
        pcm.copyInto(out, 44)
        return out
    }

    private fun writeAscii(target: ByteArray, offset: Int, text: String) {
        for (i in text.indices) target[offset + i] = text[i].code.toByte()
    }

    private fun writeIntLe(target: ByteArray, offset: Int, value: Int) {
        target[offset] = (value and 0xff).toByte()
        target[offset + 1] = (value shr 8 and 0xff).toByte()
        target[offset + 2] = (value shr 16 and 0xff).toByte()
        target[offset + 3] = (value shr 24 and 0xff).toByte()
    }

    private fun writeShortLe(target: ByteArray, offset: Int, value: Int) {
        target[offset] = (value and 0xff).toByte()
        target[offset + 1] = (value shr 8 and 0xff).toByte()
    }
}
