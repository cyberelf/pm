package net.cyberelf.reports

import kotlinx.coroutines.runBlocking
import okhttp3.OkHttpClient
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import net.cyberelf.reports.data.buildApi

/** Pins the app's DTO expectations against a real /api/state payload shape
 *  (extra fields tolerated, snake_case mapped). */
class ApiContractTest {

    private lateinit var server: MockWebServer

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    private fun fixture(): String =
        javaClass.getResourceAsStream("/state_fixture.json")!!
            .readBytes()
            .decodeToString()

    @Test
    fun `parses state payload and tolerates unknown fields`() = runBlocking {
        server.enqueue(
            MockResponse()
                .setBody(fixture())
                .setHeader("Content-Type", "application/json"),
        )
        val api = buildApi(OkHttpClient(), server.url("/").toString())

        val state = api.state()

        assertEquals(2, state.projects.size)
        assertEquals("周报工作台", state.projects[0].name)
        assertEquals("on track", state.projects[0].progressStatus)
        assertEquals("blocked", state.projects[1].progressStatus)
        assertEquals("paused", state.projects[1].status)
        assertEquals("cyberelf", state.workspaceUser)
        assertEquals("/api/state", server.takeRequest().path)
    }
}
