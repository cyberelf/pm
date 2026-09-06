package net.cyberelf.reports

import net.cyberelf.reports.voice.Wav
import org.junit.Assert.assertEquals
import org.junit.Test
import java.nio.ByteBuffer
import java.nio.ByteOrder

class WavTest {

    @Test
    fun `encodes a canonical 44-byte RIFF header`() {
        val pcm = ByteArray(100) { it.toByte() }
        val wav = Wav.encodePcmToWav(pcm, sampleRate = 16_000, channels = 1, bitsPerSample = 16)

        assertEquals(144, wav.size)
        val header = ByteBuffer.wrap(wav, 0, 44).order(ByteOrder.LITTLE_ENDIAN)
        assertEquals("RIFF", ascii(wav, 0, 4))
        assertEquals(36 + 100, header.getInt(4))
        assertEquals("WAVE", ascii(wav, 8, 4))
        assertEquals("fmt ", ascii(wav, 12, 4))
        assertEquals(16, header.getInt(16)) // fmt chunk size
        assertEquals(1, header.getShort(20).toInt()) // PCM
        assertEquals(1, header.getShort(22).toInt()) // mono
        assertEquals(16_000, header.getInt(24)) // sample rate
        assertEquals(32_000, header.getInt(28)) // byte rate: 16000 * 1 * 2
        assertEquals(2, header.getShort(32).toInt()) // block align
        assertEquals(16, header.getShort(34).toInt()) // bits
        assertEquals("data", ascii(wav, 36, 4))
        assertEquals(100, header.getInt(40))
        // payload is copied verbatim after the header
        assertEquals(0.toByte(), wav[44])
        assertEquals(99.toByte(), wav[143])
    }

    @Test
    fun `byte rate follows channel count and bit depth`() {
        val wav = Wav.encodePcmToWav(ByteArray(4), sampleRate = 44_100, channels = 2, bitsPerSample = 16)
        val header = ByteBuffer.wrap(wav).order(ByteOrder.LITTLE_ENDIAN)
        assertEquals(176_400, header.getInt(28))
        assertEquals(4, header.getShort(32).toInt())
    }

    private fun ascii(data: ByteArray, offset: Int, length: Int): String =
        String(data, offset, length, Charsets.US_ASCII)
}
