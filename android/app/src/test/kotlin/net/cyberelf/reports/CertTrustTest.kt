package net.cyberelf.reports

import net.cyberelf.reports.data.CertTrust
import net.cyberelf.reports.data.CertUntrustedException
import net.cyberelf.reports.data.PinnedTrustManager
import net.cyberelf.reports.data.ServerUrl
import net.cyberelf.reports.data.isCertProblem
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.cert.CertificateException
import javax.net.ssl.SSLPeerUnverifiedException

class CertTrustTest {

    @Test
    fun `normalizes pasted fingerprints`() {
        assertEquals(
            "a1b2c3d4".repeat(8),
            CertTrust.normalizeFingerprint("A1:B2:C3:D4:A1:B2:C3:D4:A1:B2:C3:D4:A1:B2:C3:D4:A1:B2:C3:D4:A1:B2:C3:D4:A1:B2:C3:D4:A1:B2:C3 D4"),
        )
        assertEquals("ab".repeat(32), CertTrust.normalizeFingerprint("AB".repeat(32)))
        assertNull(CertTrust.normalizeFingerprint(null))
        assertNull(CertTrust.normalizeFingerprint(""))
        assertNull(CertTrust.normalizeFingerprint("zz".repeat(32)))
        assertNull(CertTrust.normalizeFingerprint("ab".repeat(31)))
    }

    @Test
    fun `server url normalization forces scheme and trailing slash`() {
        assertEquals("https://10.200.200.3:8443/", ServerUrl.normalize("10.200.200.3:8443"))
        assertEquals("https://10.200.200.3:8443/", ServerUrl.normalize("https://10.200.200.3:8443"))
        assertEquals("https://10.200.200.3:8443/", ServerUrl.normalize(" https://10.200.200.3:8443// "))
        assertEquals("http://10.200.200.3:8765/", ServerUrl.normalize("http://10.200.200.3:8765"))
        assertEquals("", ServerUrl.normalize("   "))
    }

    @Test
    fun `pinned manager fails closed before any pin is stored`() {
        assertThrows(CertUntrustedException::class.java) {
            PinnedTrustManager(null).checkServerTrusted(arrayOf(), "TLS")
        }
    }

    @Test
    fun `pinned manager rejects empty chain`() {
        assertThrows(CertificateException::class.java) {
            PinnedTrustManager("ab".repeat(32)).checkServerTrusted(arrayOf(), "TLS")
        }
    }

    @Test
    fun `cert problem detection walks wrapped causes`() {
        assertTrue(isCertProblem(SSLPeerUnverifiedException("pin mismatch")))
        val wrapped = RuntimeException(IllegalStateException(CertUntrustedException("changed")))
        assertTrue(isCertProblem(wrapped))
        assertFalse(isCertProblem(java.net.ConnectException("refused")))
    }

    private fun assertThrows(type: Class<out Throwable>, block: () -> Unit) {
        try {
            block()
        } catch (e: Throwable) {
            if (type.isInstance(e)) return
            throw AssertionError("expected ${type.simpleName}, got ${e.javaClass.simpleName}", e)
        }
        throw AssertionError("expected ${type.simpleName} but nothing was thrown")
    }
}
