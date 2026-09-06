package net.cyberelf.reports

import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import net.cyberelf.reports.data.CertTrust
import net.cyberelf.reports.data.ConflictResponse
import net.cyberelf.reports.data.ServerUrl
import net.cyberelf.reports.data.VoiceRepository
import net.cyberelf.reports.data.VoiceSubmitResult
import net.cyberelf.reports.data.buildApi
import okhttp3.OkHttpClient
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.util.Base64

/** Exercises the voice flow against the real request/response shapes:
 *  base64 wav upload, 2s-start polling with injected sleeps, 409 takeover. */
class VoiceFlowTest {

    private lateinit var server: MockWebServer
    private val slept = mutableListOf<Long>()

    private fun repository(): VoiceRepository {
        val api = buildApi(
            CertTrust.okHttpClient(null), // http MockWebServer bypasses TLS
            server.url("/").toString(),
        )
        return VoiceRepository(apiProvider = { api }, pollSleep = { slept += it })
    }

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()
        slept.clear()
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun `audio upload posts base64 wav and polls to completion`() = runBlocking {
        val wav = ByteArray(64) { 0x55 }
        val encoded = Base64.getEncoder().encodeToString(wav)
        server.enqueue(
            MockResponse().setResponseCode(202)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"id": 7, "status": "transcribing"}"""),
        )
        server.enqueue(jobResponse(7, "transcribing"))
        server.enqueue(jobResponse(7, "structuring"))
        server.enqueue(
            jobResponse(
                7,
                "completed",
                transcript = "修一下登录页",
                todoIds = "[3, 4]",
                fallback = 0,
            ),
        )

        val submitted = repository().submitAudio(wav)
        assertTrue(submitted is VoiceSubmitResult.Submitted)
        assertEquals(7L, (submitted as VoiceSubmitResult.Submitted).jobId)

        var stage = ""
        val job = repository().pollUntilDone(7) { stage = it }
        assertEquals("completed", job.status)
        assertEquals(listOf(3L, 4L), job.todoIds)
        assertEquals("修一下登录页", job.transcript)
        assertEquals(false, job.didFallback)

        // request shape: the body must carry base64 wav with wav content type
        val body = server.takeRequest().body.readUtf8()
        val json = Json.parseToJsonElement(body).jsonObject
        assertEquals(encoded, json["audio_base64"]!!.jsonPrimitive.content)
        assertEquals("audio/wav", json["content_type"]!!.jsonPrimitive.content)

        assertEquals("/api/voice-jobs/7", server.takeRequest().path)
        server.takeRequest()
        assertEquals("/api/voice-jobs/7", server.takeRequest().path)
        // injected sleeps: starts at 2s and climbs toward the 5s cap
        assertEquals(listOf(2000L, 3000L), slept)
    }

    @Test
    fun `http 409 parses the active job id for takeover`() = runBlocking {
        server.enqueue(
            MockResponse().setResponseCode(409)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"error": "another voice job is already running", "active_job_id": 3}"""),
        )

        val result = repository().submitText("hi")
        assertTrue(result is VoiceSubmitResult.Conflict)
        assertEquals(3L, (result as VoiceSubmitResult.Conflict).activeJobId)
    }

    @Test
    fun `oversized audio is rejected locally without a request`() = runBlocking {
        val big = ByteArray(VoiceRepository.MAX_AUDIO_BYTES + 1)
        val result = repository().submitAudio(big)
        assertTrue(result is VoiceSubmitResult.Rejected)
        assertEquals(0, server.requestCount)
    }

    @Test
    fun `transient poll failures keep polling`() = runBlocking {
        server.enqueue(jobResponse(9, "transcribing"))
        server.enqueue(MockResponse().setResponseCode(500).setBody("boom"))
        server.enqueue(jobResponse(9, "completed"))

        val job = repository().pollUntilDone(9)
        assertEquals("completed", job.status)
        assertEquals(listOf(2000L, 3000L), slept)
    }

    private fun jobResponse(
        id: Long,
        status: String,
        transcript: String = "",
        todoIds: String = "[]",
        fallback: Int = 0,
    ): MockResponse =
        MockResponse().setResponseCode(200)
            .setHeader("Content-Type", "application/json")
            .setBody(
                """
                {
                  "id": $id,
                  "status": "$status",
                  "transcript": "$transcript",
                  "error": "",
                  "fallback": $fallback,
                  "todo_ids": $todoIds,
                  "created_at": "2026-09-06T10:00:00+08:00",
                  "updated_at": "2026-09-06T10:00:10+08:00"
                }
                """.trimIndent(),
            )
}
